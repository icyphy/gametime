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

//It actually printf the cycle count instead
void insertPrintTimestampLogic(LLVMContext& context, Module* module, IRBuilder<>& builder) {
    // Declare the external 'printf' function
    std::vector<Type*> printfArgTypes;
    printfArgTypes.push_back(Type::getInt8PtrTy(context)); // 'printf' requires a format string
    FunctionType* printfType = FunctionType::get(Type::getInt32Ty(context), printfArgTypes, true); // 'true' for varargs
    FunctionCallee printfFunc = module->getOrInsertFunction("printf", printfType);

    // Define the format string for 'printf'
    Constant *formatStr = builder.CreateGlobalStringPtr("%lld\n", "formatStr");

    // Declare the llvm.readcyclecounter intrinsic
    Function* nowFunc = Intrinsic::getDeclaration(module, Intrinsic::readcyclecounter);

    // Call the 'llvm.readcyclecounter' intrinsic to get the current time
    Value* nowVal = builder.CreateCall(nowFunc, {}, "nowVal");

    // Call 'printf' to print the time
    builder.CreateCall(printfFunc, {formatStr, nowVal});
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
    insertPrintTimestampLogic(context, module, builder);
    builder.CreateCall(targetFunction, preparedArgs);
    insertPrintTimestampLogic(context, module, builder);
    
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
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <path to .bc file> <function name> <path to .txt values file>" << std::endl;
        return 1;
    }

    std::string bitcodeFilePath = argv[1];
    std::string targetFunctionName = argv[2];
    std::string valuesFilePath = argv[3];

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
    llvm::raw_fd_ostream OS("modified_output.bc", EC, llvm::sys::fs::OF_None);
    if (EC) {
        llvm::errs() << "Could not open file: " << EC.message();
        return 1;
    }
    llvm::WriteBitcodeToFile(*module, OS);

    return 0;
}