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

static std::string getSimpleNodeLabel(const BasicBlock *Node,
                                      const Function *) {
    if (!Node->getName().empty())
        return Node->getName().str();

    std::string Str;
    raw_string_ostream OS(Str);

    Node->printAsOperand(OS, false);
    return OS.str();
}

// void insertGlobalVariables(Module *module, const vector<int> &labels) {
//     LLVMContext &context = module->getContext();
//     int counter = 0;
//     for (Function &F : *module) {
//         for (BasicBlock &BB : F) {
//             string labelString = getSimpleNodeLabel(&BB,&F);
//             //cerr << labelString <<endl;
//             //BB.printAsOperand(errs(), false);
//             int label = stoi(labelString.substr(1));
            // if (find(labels.begin(), labels.end(), label) != labels.end()) {
            //     IRBuilder<> builder(BB.getFirstNonPHI());
            //     GlobalVariable *GV = module->getGlobalVariable("conditional_var_" + to_string(counter));
            //     if (!GV) {
            //         GV = new GlobalVariable(*module,
            //                                 IntegerType::get(context, 8),
            //                                 false,
            //                                 GlobalValue::ExternalLinkage,
            //                                 ConstantInt::get(IntegerType::get(context, 8), 0),
            //                                 "conditional_var_" + to_string(counter));
            //     }
            //     builder.CreateStore(ConstantInt::get(IntegerType::get(context, 8), 1), GV);
            //     counter++;
            // }
//         }
//     }
// }
int extractLastNumber(const std::string& str) {
    size_t lastPercentPos = str.rfind('%');
    if (lastPercentPos != std::string::npos) {
        std::string lastNumberStr = str.substr(lastPercentPos + 1);
        return std::stoi(lastNumberStr);
    }
    return -1; // In case no '%' is found, which should not happen in your context
}

void insertGlobalVariables(Module *module, const vector<int> &labels) {
    LLVMContext &context = module->getContext();
    int counter = 0;
    int counter_bad_bb = labels.size();

    for (Function &F : *module) {
        for (BasicBlock &BB : F) {
            // Assuming you have a way to convert BasicBlock to an int label
            std::string blockLabelString = getSimpleNodeLabel(&BB, &F);
            // Attempt to convert the block label string to an integer
            // Ensure this logic matches how your block labels are represented
            int blockLabel = extractLastNumber(blockLabelString);;
            if (blockLabel != -1 && std::find(labels.begin(), labels.end(), blockLabel) != labels.end()) {
                // Check if this block's label is in the labels list
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
                } else {
                    IRBuilder<> builder(BB.getFirstNonPHI());
                    GlobalVariable *GV = module->getGlobalVariable("conditional_var_" + to_string(counter_bad_bb ));
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



void writeLLFile(Module *module, const string &filename) {
    std::error_code EC;
    raw_fd_ostream outputFile(filename, EC, sys::fs::OF_None);
    if (EC) {
        cerr << "Error opening file: " << EC.message() << endl;
        return;
    }

    module->print(outputFile, nullptr);
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
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <input.c> <labels.txt>" << endl;
        return 1;
    }
    string inputFilename(argv[1]);
    string labelsFilename(argv[2]);
    string outputFilenameMod = inputFilename.substr(0, inputFilename.size() - 2) + "_mod";
    string outputFilename = inputFilename.substr(0, inputFilename.size() - 2);
    LLVMContext context;
    SMDiagnostic error;

    // Compile the input C file to LLVM bitcode
    string compileCommand = "clang -emit-llvm -c " + string(argv[1]) + " -o " + outputFilename + ".bc";
    int compileResult = system(compileCommand.c_str());
    if (compileResult != 0) {
        cerr << "Failed to compile the input C file to LLVM bitcode." << endl;
        return 1;
    }

    // Parse the LLVM bitcode file
    unique_ptr<Module> module = parseIRFile(outputFilename + ".bc", error, context);
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

    // Insert global variables into basic blocks with conditional branches
    insertGlobalVariables(module.get(), labels);

    // Write normal bitcode to a file
    // std::error_code EC_normal;
    // raw_fd_ostream normalOutputFile((outputFilename + "_normal.bc").c_str(), EC_normal, sys::fs::OF_None);
    // if (EC_normal) {
    //     cerr << "Error opening normal bitcode file: " << EC_normal.message() << endl;
    //     return 1;
    // }
    // WriteBitcodeToFile(*originalModule, normalOutputFile);
    // if (EC_normal) {
    //     cerr << "Error writing normal bitcode: " << EC_normal.message() << endl;
    //     return 1;
    // }

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