#include <iostream>
#include <string>
#include <fstream>
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
#include <llvm/IR/InlineAsm.h>

using namespace llvm;
using namespace std;
// COMPILE THIS WITH: clang++ generate_executable.cpp `llvm-config --cxxflags --ldflags --libs --system-libs` -o generate_executable

// ARMv8 Assumed

// PMCCNTR_EL0 - Performance Monitors Cycle Count Register. Counts the actual cycles executed by the processor. Effected by CPU Frequency scaling
// void insertPrintTimestampLogicPMCCNTR(LLVMContext& context, Module* module, IRBuilder<>& builder) {
//     Type *i64Type = Type::getInt64Ty(context);
//     FunctionType *asmFuncType = FunctionType::get(i64Type, {}, false);
    
//     // Using pmccntr_el0, the physical counter
//     auto readCycleCountPMCCNTR = InlineAsm::get(asmFuncType, "mrs %0, pmccntr_el0", "=r", true);
    
//     Value *cycleCountPMCCNTR = builder.CreateCall(readCycleCountPMCCNTR, {});

//     FunctionCallee printfFunc = module->getOrInsertFunction("printf",
//         FunctionType::get(Type::getInt32Ty(context), {Type::getInt8PtrTy(context)}, true));

//     builder.CreateCall(printfFunc, {builder.CreateGlobalStringPtr("PMCCNTR Cycle count: %lld\n"), cycleCountPMCCNTR});
// }

// CNTPCT_EL0 - Physical Count Register. Provides the count value of the system counter, which increments at a frequency specified by CNTFRQ_EL0. It's a virtual counter that runs at a constant frequency, unaffected by CPU power states (e.g., sleep or throttle).
// void insertPrintTimestampLogicCNTPCT(LLVMContext& context, Module* module, IRBuilder<>& builder) {
//     // Inline assembly to read the physical counter on ARMv8
//     Type *i64Type = Type::getInt64Ty(context);
//     FunctionType *asmFuncType = FunctionType::get(i64Type, false);
    
//     // Inline assembly to read CNTPCT_EL0. The constraint string "=r" indicates an output operand.
//     // Note: The "=r" constraint tells LLVM to use a general-purpose register for output.
//     auto readCycleCountCNTPCT = InlineAsm::get(asmFuncType, "mrs x0, cntpct_el0", "=r", true);
    
//     // Insert the assembly instruction and capture its return value
//     Value *cycleCountCNTPCT = builder.CreateCall(readCycleCountCNTPCT);
    
//     // For demonstration, just print the cycle count directly
//     // You would typically handle the cycle count in a way that suits your application,
//     // such as storing it for later comparison or calculation.
//     FunctionCallee printfFunc = module->getOrInsertFunction("printf",
//         FunctionType::get(Type::getInt32Ty(context), {Type::getInt8PtrTy(context)}, true));
//     builder.CreateCall(printfFunc, {builder.CreateGlobalStringPtr("CNTPCT Cycle count: %lld\n"), cycleCountCNTPCT});
// }

// CNTVCT_EL0 (Counter-timer Virtual Count register) is a register in ARMv8 that provides the count of virtual cycles.
void insertPrintTimestampLogicCNTVCT(LLVMContext& context, Module* module, IRBuilder<>& builder) {
    // Inline assembly to read the virtual counter on ARMv8
    // Note: The type of the inline asm must match what it returns (i.e., a 64-bit integer for the cycle count)
    Type *i64Type = Type::getInt64Ty(context);
    FunctionType *asmFuncType = FunctionType::get(i64Type, false);
    
    // The constraint string "={x0}" tells LLVM that x0 is an output operand.
    // The "r" constraint code could be used for inputs. This example has no inputs.
    auto readCycleCount = InlineAsm::get(asmFuncType, "mrs x0, cntvct_el0", "=r", true);
    
    // Insert the assembly instruction and capture its return value
    Value *cycleCount = builder.CreateCall(readCycleCount);
    
    // print the cycle count directly as a placeholder
    builder.CreateCall(module->getOrInsertFunction("printf",
        FunctionType::get(Type::getInt32Ty(context), {Type::getInt8PtrTy(context)}, true)),
        {builder.CreateGlobalStringPtr("Cycle count: %lld\n"), cycleCount});
}

void insertGlobalVariablesAndModifyMain(Module *module, const string &functionName, const vector<int> &values) {
    LLVMContext &context = module->getContext();
    IRBuilder<> builder(context);
    vector<GlobalVariable *> globalVars;

    // Create global variables
    for (int i = 0; i < values.size(); ++i) {
        std::string varName = "globalVar" + std::to_string(i);
        //TODO: generalize to handle more than Int32. Maybe combine with parsing part.
        globalVars.push_back(new GlobalVariable(*module, 
                                                builder.getInt32Ty(), 
                                                false, 
                                                GlobalValue::ExternalLinkage, 
                                                builder.getInt32(values[i]), 
                                                varName));
    }

    // Find the target function
    Function *targetFunction = module->getFunction(functionName);
    if (!targetFunction) {
        cerr << "Target function " << functionName << " not found." << endl;
        exit(1);
    }

    FunctionType* funcType = targetFunction->getFunctionType();
    size_t numParams = funcType->getNumParams();

    if (numParams != values.size()) {
        errs() << "Wrong number of arguments.\n";
        exit(1);
    }

    // Find or create the main function
    Function *mainFunction = module->getFunction("main");
    if (!mainFunction) {
        // Main function prototype (int main())
        FunctionType *funcType = FunctionType::get(builder.getInt32Ty(), false);
        mainFunction = Function::Create(funcType, Function::ExternalLinkage, "main", module);
        BasicBlock *entry = BasicBlock::Create(context, "entry", mainFunction);
        builder.SetInsertPoint(entry);
        builder.CreateRet(builder.getInt32(0));
    }


    // Modify the main function
    BasicBlock &entryBlock = mainFunction->getEntryBlock();
    builder.SetInsertPoint(entryBlock.getFirstNonPHI());

    std::vector<Value*> preparedArgs;
    //This has to happen after insert point
    //TODO: we might want to add type checks and handle
    for (size_t i = 0; i < numParams; ++i) {
        Type* paramType = funcType->getParamType(i);
        auto *loadedValue = builder.CreateLoad(paramType, globalVars[i]);
        preparedArgs.push_back(loadedValue);
    }

    // Insert timing function calls and call to target function
    insertPrintTimestampLogicCNTVCT(context, module, builder);
    builder.CreateCall(targetFunction, preparedArgs);
    insertPrintTimestampLogicCNTVCT(context, module, builder);
    
}

vector<int> parseIntegerFromFile(const string &filepath) {
    vector<int> values;
    ifstream file(filepath);
    if (!file.is_open()) {
        cerr << "Error: Unable to open file " << filepath << endl;
        exit(1);
    }
    int value;
    while (file >> value) {
        values.push_back(value);
    }
    file.close();
    return values;
}


int main(int argc, char **argv) {
    if (argc < 4) {
        std::cerr << "Usage: " << argv[0] << " <path to .bc file> <function name> <path to .txt values file> <output folder>" << std::endl;
        return 1;
    }

    std::string bitcodeFilePath = argv[1];
    std::string targetFunctionName = argv[2];
    std::string valuesFilePath = argv[3];
    std::string outputFolderPath = argv[4];

    //TODO: Handle general inputs based on function argument types
    std::vector<int> values;
    values = parseIntegerFromFile(valuesFilePath);

    // ... Code to initialize LLVM and load the bitcode file ...
    LLVMContext context;
    SMDiagnostic error;
    std::unique_ptr<Module> module = parseIRFile(bitcodeFilePath, error, context);

    if (!module) {
        error.print(argv[0], errs());
        std::cerr << "Error: Failed to parse input LLVM bitcode file." << std::endl;
        return 1;
    }

    // Modify the module
    insertGlobalVariablesAndModifyMain(module.get(), targetFunctionName, values);

    // Write the modified module to a new bitcode file
    std::error_code EC;
    llvm::raw_fd_ostream OS(outputFolderPath + "/modified_output.bc", EC, llvm::sys::fs::OF_None);
    
    if (EC) {
        llvm::errs() << "Could not open file: " << EC.message();
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, OS);

    return 0;
}