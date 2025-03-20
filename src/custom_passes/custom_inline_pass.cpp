#include "llvm/IR/PassManager.h"    
#include "llvm/IR/Module.h"         
#include "llvm/IR/Function.h"      
#include "llvm/IR/Attributes.h"    
#include "llvm/Support/raw_ostream.h"
#include "llvm/Support/CommandLine.h" 
#include "llvm/Passes/PassPlugin.h"   
#include "llvm/Passes/PassBuilder.h" 


using namespace llvm;


static cl::opt<std::string> AnalysedFunction("analysed-func", 
                                            cl::desc("Function to exclude from inlining"),
                                            cl::value_desc("function name"),
                                            cl::Required);

struct CustomInlinePass : public PassInfoMixin<CustomInlinePass> {

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        bool changed = false;

        for (Function &F : M) {
            if (F.getName() == AnalysedFunction) {
                F.removeFnAttr(Attribute::AlwaysInline);
                F.addFnAttr(Attribute::NoInline);
                errs() << "Function " << F.getName() << " is not inlined.\n";
                changed = true;
            } else {
                F.removeFnAttr(Attribute::NoInline);
                F.addFnAttr(Attribute::AlwaysInline);
                errs() << "Function " << F.getName() << " is inlined.\n";
                changed = true;
            }
        }
        return changed ? PreservedAnalyses::none() : PreservedAnalyses::all();
    }
};


extern "C" LLVM_ATTRIBUTE_WEAK PassPluginLibraryInfo llvmGetPassPluginInfo() {
  return {
    LLVM_PLUGIN_API_VERSION, "CustomInlinePass", "v0.1",
    [](PassBuilder &PB) {
      PB.registerPipelineParsingCallback(
        [](StringRef Name, ModulePassManager &MPM,
           ArrayRef<PassBuilder::PipelineElement>) {
          if (Name == "custom-inline") {
            MPM.addPass(CustomInlinePass());
            return true;
          }
          return false;
        }
      );
    }
  };
}



