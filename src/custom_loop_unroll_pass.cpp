#include "llvm/Analysis/AliasAnalysis.h"
#include "llvm/Analysis/AssumptionCache.h"
#include "llvm/Analysis/LoopAnalysisManager.h"
#include "llvm/Analysis/LoopInfo.h"
#include "llvm/Analysis/ScalarEvolution.h"
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/IRPrintingPasses.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/InitLLVM.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/Transforms/Scalar/LoopPassManager.h"
#include "llvm/Transforms/Utils/LoopUtils.h"
#include "llvm/Transforms/Utils/UnrollLoop.h"
#include <iostream>

using namespace llvm;
using namespace std;

static cl::opt<std::string> InputFilename(cl::Positional, cl::desc("<input .bc file>"), cl::Required);
static cl::opt<std::string> OutputFilename("o", cl::desc("Specify output filename"), cl::value_desc("output file"), cl::Required);

// Helper function to extract the unroll count from loop metadata
unsigned getUnrollCountFromMetadata(const Loop* L) {
    if (MDNode* LoopMD = L->getLoopID()) {
        for (const MDOperand &Op : LoopMD->operands()) {
            if (MDNode* MD = dyn_cast<MDNode>(Op)) {
                if (MDString* S = dyn_cast<MDString>(MD->getOperand(0))) {
                    if (S->getString().startswith("llvm.loop.unroll.count")) {
                        if (Metadata* UnrollCountMD = MD->getOperand(1)) {
                            if (ConstantAsMetadata* CAM = dyn_cast<ConstantAsMetadata>(UnrollCountMD)) {
                                if (ConstantInt* CI = dyn_cast<ConstantInt>(CAM->getValue())) {
                                    return CI->getZExtValue();
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return 1; // Default to not unrolling if no metadata is present
}

class CustomLoopUnrollPass : public PassInfoMixin<CustomLoopUnrollPass> {
public:
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM);
};

PreservedAnalyses CustomLoopUnrollPass::run(Function &F, FunctionAnalysisManager &AM) {
  auto &LI = AM.getResult<LoopAnalysis>(F);
  auto &SE = AM.getResult<ScalarEvolutionAnalysis>(F);
  auto &DT = AM.getResult<DominatorTreeAnalysis>(F);
  auto &AC = AM.getResult<AssumptionAnalysis>(F);
  auto &TTI = AM.getResult<TargetIRAnalysis>(F);
  auto &ORE = AM.getResult<OptimizationRemarkEmitterAnalysis>(F);

  for (auto &L : LI) {
    unsigned UnrollCount = getUnrollCountFromMetadata(L);

    if (UnrollCount > 1) {

        UnrollLoopOptions ULO;
        ULO.Count = UnrollCount;
        ULO.Force = true;
        ULO.AllowExpensiveTripCount = true;
        ULO.UnrollRemainder = true;

        Loop *CurrentLoop = L;
        bool unrolledAtLeastOnce = false;

        while (CurrentLoop != nullptr) {
            Loop *RemainderLoop = nullptr;
            auto UnrollResult = UnrollLoop(CurrentLoop, ULO, &LI, &SE, &DT, &AC, &TTI, &ORE, true, &RemainderLoop);
            cout << "Unroll attempt";
            if (UnrollResult == llvm::LoopUnrollResult::FullyUnrolled || UnrollResult == llvm::LoopUnrollResult::PartiallyUnrolled) {
                unrolledAtLeastOnce = true;
                // Prepare for the next iteration to attempt to unroll the remainder loop, if any.
                CurrentLoop = RemainderLoop;
            } else {
                // If the loop wasn't unrolled or we cannot proceed further, break out of the loop.
                break;
            }
        }

        if (unrolledAtLeastOnce) {
            // Indicate that changes were made and certain analyses might be invalidated.
            return PreservedAnalyses::none();
        }
    }
  }

  return PreservedAnalyses::all();
}


int main(int argc, char **argv) {
    InitLLVM X(argc, argv);
    cl::ParseCommandLineOptions(argc, argv, "LLVM New PM Loop Unroller\n");

    LLVMContext Context;
    SMDiagnostic Err;

    // Load the input module
    auto M = parseIRFile(InputFilename, Err, Context);
    if (!M) {
        Err.print(argv[0], errs());
        return 1;
    }

    PassBuilder PB;
    FunctionAnalysisManager FAM;
    PB.registerFunctionAnalyses(FAM);

    FunctionPassManager FPM;
    FPM.addPass(CustomLoopUnrollPass());

    // Apply the pass to each function in the module
    for (Function &F : *M) {
        FPM.run(F, FAM);
    }

    // Output the modified module
    std::error_code EC;
    raw_fd_ostream OS(OutputFilename, EC, sys::fs::OF_None);
    if (EC) {
        errs() << "Could not open file: " << EC.message();
        return 1;
    }

    WriteBitcodeToFile(*M, OS);

    return 0;
}