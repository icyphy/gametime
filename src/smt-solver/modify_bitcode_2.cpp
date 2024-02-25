#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/TargetSelect.h>
#include <llvm/Bitcode/BitcodeWriter.h>
#include <llvm/Bitcode/BitcodeReader.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Transforms/Utils/Cloning.h>
#include <llvm/Transforms/IPO/PassManagerBuilder.h>

using namespace llvm;
using namespace std;

void insertGlobalVariables(Module *module, const vector<int> &labels) {
    LLVMContext &context = module->getContext();
    int counter = 0;
    for (Function &F : *module) {
        for (BasicBlock &BB : F) {
            int label = stoi(BB.getName().substr(1));
            if (find(labels.begin(), labels.end(), label) != labels.end()) {
                IRBuilder<> builder(BB.getFirstNonPHI());
                GlobalVariable *GV = module->getGlobalVariable("conditional_var_" + to_string(counter));
                if (!GV) {
                    GV = new GlobalVariable(*module,
                                            IntegerType::get(context, 8),
                                            false,
                                            GlobalValue::ExternalLinkage,
                                            ConstantInt::get(IntegerType::get(context, 8), 0),
                                            "conditional_var_" + to_string(counter));
                }
                builder.CreateStore(ConstantInt::get(IntegerType::get(context, 8), 1), GV);
                counter++;
            }
        }
    }
}

vector<int> parseLabelsFromFile(const string &filename) {
    vector<int> labels;
    ifstream file(filename);
    if (!file.is_open()) {
        cerr << "Error: Unable to open file " << filename << endl;
        exit(1);
    }
    int label;
    while (file >> label) {
        labels.push_back(label);
    }
    file.close();
    return labels;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <input.bc> <labels.txt>" << endl;
        return 1;
    }
    string inputFilename(argv[1]);
    string labelsFilename(argv[2]);
    string outputFilenameMod = inputFilename.substr(0, inputFilename.size() - 3) + "_mod.bc";

    LLVMContext context;
    SMDiagnostic error;

    // Parse the LLVM bitcode file
    unique_ptr<Module> module = parseIRFile(inputFilename, error, context);
    if (!module) {
        error.print(argv[0], errs());
        cerr << "Error: Failed to parse input LLVM bitcode file." << endl;
        return 1;
    }

    // Verify the module
    if (verifyModule(*module, &errs())) {
        cerr << "Error: Invalid module" << endl;
        return 1;
    }

    // Parse labels from file
    vector<int> labels = parseLabelsFromFile(labelsFilename);

    // Insert global variables into basic blocks with matching labels
    insertGlobalVariables(module.get(), labels);

    // Write modified bitcode to a file
    std::error_code EC_modified;
    raw_fd_ostream modifiedOutputFile(outputFilenameMod.c_str(), EC_modified, sys::fs::OF_None);
    if (EC_modified) {
        cerr << "Error opening modified bitcode file: " << EC_modified.message() << endl;
        return 1;
    }
    WriteBitcodeToFile(*module, modifiedOutputFile);
    if (EC_modified) {
        cerr << "Error writing modified bitcode: " << EC_modified.message() << endl;
        return 1;
    }

    return 0;
}
