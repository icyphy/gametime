#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Transforms/Utils/Cloning.h>
#include <llvm/Transforms/Utils/FunctionComparator.h>
// #include <llvm/Transforms/Utils/InlineFunction.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/InstIterator.h>
#include <llvm/Support/FileSystem.h>
#include <llvm/Support/CommandLine.h>
#include <llvm/Bitcode/BitcodeWriter.h>
#include <llvm/Bitcode/BitcodeReader.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/InitLLVM.h>
#include <llvm/Linker/Linker.h>
#include <llvm/Passes/PassBuilder.h>
#include <llvm/Pass.h>
#include <llvm/Transforms/IPO/Inliner.h>

using namespace llvm;

void runInliner(Module &M) {
    PassBuilder PB;
    LoopAnalysisManager LAM;
    FunctionAnalysisManager FAM;
    CGSCCAnalysisManager CGAM;
    ModuleAnalysisManager MAM;

    // Register all the basic analyses with the managers.
    PB.registerModuleAnalyses(MAM);
    PB.registerCGSCCAnalyses(CGAM);
    PB.registerFunctionAnalyses(FAM);
    PB.registerLoopAnalyses(LAM);
    PB.crossRegisterProxies(LAM, FAM, CGAM, MAM);

    ModulePassManager MPM;
    MPM.addPass(createModuleToPostOrderCGSCCPassAdaptor(InlinerPass()));

    // Run the passes
    MPM.run(M, MAM);
}

void inlineExternalFunctions(Module &MainModule) {
    runInliner(MainModule);
}

int main(int argc, char **argv) {
    // Initialize LLVM
    InitLLVM X(argc, argv);

    // Parse command-line arguments
    cl::opt<std::string> MainFile(cl::Positional, cl::desc("<main bitcode file>"), cl::Required);
    cl::list<std::string> ExternalFiles(cl::Positional, cl::desc("<external bitcode files>"), cl::OneOrMore);
    cl::ParseCommandLineOptions(argc, argv);

    LLVMContext Context;
    SMDiagnostic Err;

    // Load the main module
    std::unique_ptr<Module> MainModule = parseIRFile(MainFile, Err, Context);
    if (!MainModule) {
        Err.print(argv[0], errs());
        return 1;
    }

    // Link external modules
    for (const auto &File : ExternalFiles) {
        std::unique_ptr<Module> ExternalModule = parseIRFile(File, Err, Context);
        if (!ExternalModule) {
            Err.print(argv[0], errs());
            return 1;
        }

        if (Linker::linkModules(*MainModule, std::move(ExternalModule))) {
            errs() << "Error linking external module: " << File << "\n";
            return 1;
        }
    }

    // Inline external functions
    inlineExternalFunctions(*MainModule);

    // Verify the final module
    if (verifyModule(*MainModule, &errs())) {
        errs() << "Module verification failed\n";
        return 1;
    }

    // Write the final module to a new bitcode file
    std::error_code EC;
    raw_fd_ostream Out("inlined.bc", EC, sys::fs::OF_None);
    WriteBitcodeToFile(*MainModule, Out);
    Out.flush();

    return 0;
}


//clang -emit-llvm -O0 -c helper.c -o helper.bc
//clang -emit-llvm -O0 -c ext_func.c -o ext_func.bc
// clang++ -g -O3 `llvm-config --cxxflags --ldflags --system-libs --libs all` -o inline_functions inline_functions.cpp
// ./inline_functions ext_func.bc helper.bc
// opt -dot-cfg inlined.bc
// dot -Tpng .main.dot -o cfg_main.png


