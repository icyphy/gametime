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

/**
 * Returns a simple label for a BasicBlock, using its name if available,
 * or otherwise printing it as an operand.
 *
 * @param Node - The BasicBlock for which to generate a label.
 * @param Function - The function containing the BasicBlock.
 * @return A string representing the label of the BasicBlock.
 */
static std::string getSimpleNodeLabel(const BasicBlock *Node, const Function *) {
    if (!Node->getName().empty())
        return Node->getName().str();

    std::string Str;
    raw_string_ostream OS(Str);

    Node->printAsOperand(OS, false);
    return OS.str();
}

/**
 * Extracts the last number following a '%' character in a string.
 *
 * @param str - The input string from which to extract the number.
 * @return The extracted number, or -1 if '%' is not found.
 */
int extractLastNumber(const std::string& str) {
    size_t lastPercentPos = str.rfind('%');
    if (lastPercentPos != std::string::npos) {
        std::string lastNumberStr = str.substr(lastPercentPos + 1);
        return std::stoi(lastNumberStr);
    }
    return -1; // In case no '%' is found, which should not happen in your context
}

/**
 * Inserts global variables into the specified basic blocks based on the provided labels.
 *
 * @param module - The LLVM module containing the functions and basic blocks.
 * @param labels - A vector of labels where global variables should be inserted.
 * @param allLabels - A vector of all possible labels in the function.
 * @param functionName - The name of the function where the global variables will be inserted.
 */
void insertGlobalVariables(Module *module, const vector<int> &labels, const vector<int> &allLabels, const string &functionName) {
    LLVMContext &context = module->getContext();
    int counter = 0;
    int counter_bad_bb = labels.size();

    for (Function &F : *module) {
        if (F.getName().str() != functionName) {
            continue;
        }
        for (BasicBlock &BB : F) {
            // Convert BasicBlock label to an integer
            std::string blockLabelString = getSimpleNodeLabel(&BB, &F);
            int blockLabel = extractLastNumber(blockLabelString);

            if (blockLabel != -1) {
                // Insert global variables based on the label's presence in labels or allLabels
                if (find(labels.begin(), labels.end(), blockLabel) != labels.end()) {
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
                } else if (find(allLabels.begin(), allLabels.end(), blockLabel) != allLabels.end()) {
                    IRBuilder<> builder(BB.getFirstNonPHI());
                    GlobalVariable *GV = module->getGlobalVariable("conditional_var_" + to_string(counter_bad_bb));
                    if (!GV) {
                        GV = new GlobalVariable(*module,
                                                IntegerType::get(context, 8),
                                                false,
                                                GlobalValue::ExternalLinkage,
                                                ConstantInt::get(IntegerType::get(context, 8), 0),
                                                "conditional_var_" + to_string(counter_bad_bb));
                    }
                    builder.CreateStore(ConstantInt::get(IntegerType::get(context, 8), 0), GV);
                    counter_bad_bb++;
                }
            }
        }
    }
}

/**
 * Writes the LLVM assembly representation of the module to a file.
 *
 * @param module - The LLVM module to be written.
 * @param filename - The name of the file to write the LLVM assembly to.
 */
void writeLLFile(Module *module, const string &filename) {
    std::error_code EC;
    raw_fd_ostream outputFile(filename, EC, sys::fs::OF_None);
    if (EC) {
        cerr << "Error opening file: " << EC.message() << endl;
        return;
    }

    module->print(outputFile, nullptr);
}

/**
 * Reads labels from a file and returns them as a vector of integers.
 *
 * @param filename - The name of the file containing the labels.
 * @return A vector of integers representing the labels.
 */
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

/**
 * Main function to parse the LLVM bitcode file, insert global variables based on labels,
 * and write the modified and original LLVM assembly and bitcode to files.
 *
 * @param argc - The number of command-line arguments.
 * @param argv - The array of command-line arguments.
 * @return 0 on success, 1 on failure.
 */
int main(int argc, char **argv) {
    if (argc < 5) {
        cerr << "Usage: " << argv[0] << " <input.bc> <labels.txt> <all_labels.txt> funcName" << endl;
        return 1;
    }
    string inputFilename(argv[1]);
    string labelsFilename(argv[2]);
    string allLabelsFilename(argv[3]);
    string funcName(argv[4]);
    string outputFilenameMod = inputFilename.substr(0, inputFilename.size() - 3) + "_mod";
    string outputFilename = inputFilename.substr(0, inputFilename.size() - 3);
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

    // Create a copy of the original module
    unique_ptr<Module> originalModule = CloneModule(*module);

    // Parse labels from file
    vector<int> labels = parseLabelsFromFile(labelsFilename);
    vector<int> allLabels = parseLabelsFromFile(allLabelsFilename);

    // Insert global variables into basic blocks with conditional branches
    insertGlobalVariables(module.get(), labels, allLabels, funcName);

    // Write modified bitcode to a file
    std::error_code EC_modified;
    raw_fd_ostream modifiedOutputFile((outputFilenameMod + ".bc").c_str(), EC_modified, sys::fs::OF_None);
    if (EC_modified) {
        cerr << "Error opening modified bitcode file: " << EC_modified.message() << endl;
        return 1;
    }
    WriteBitcodeToFile(*module, modifiedOutputFile);
    if (EC_modified) {
        cerr << "Error writing modified bitcode: " << EC_modified.message() << endl;
        return 1;
    }

    // Write normal LLVM assembly to a file
    writeLLFile(originalModule.get(), (outputFilename + ".ll").c_str());

    // Write modified LLVM assembly to a file
    writeLLFile(module.get(), (outputFilenameMod + ".ll").c_str());

    return 0;
}
