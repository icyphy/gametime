; ModuleID = '/opt/project/test/test_flexpret_simulator/programs/add/addgt/addgtinlined.bt'
source_filename = "/opt/project/test/test_flexpret_simulator/programs/add/add.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: nounwind uwtable
define dso_local i32 @add(i32 noundef %0, i32 noundef %1) #0 {
  %3 = add i32 %0, %1
  ret i32 %3
}

; Function Attrs: nounwind uwtable
define dso_local i32 @main() #0 {
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 -1163216214) #2, !srcloc !4
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 1) #2, !srcloc !5
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 -1163216214) #2, !srcloc !4
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 2) #2, !srcloc !5
  %1 = add i32 2, 10
  %2 = icmp ult i32 1, %1
  br i1 %2, label %3, label %5

3:                                                ; preds = %0
  %4 = add i32 1, 2
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 -1163216214) #2, !srcloc !4
  call void asm sideeffect "csrw 0x51e, $0", "r,~{dirflag},~{fpsr},~{flags}"(i32 %4) #2, !srcloc !5
  br label %5

5:                                                ; preds = %3, %0
  ret i32 0
}

; Function Attrs: argmemonly nofree nosync nounwind willreturn
declare void @llvm.lifetime.start.p0i8(i64 immarg, i8* nocapture) #1

; Function Attrs: argmemonly nofree nosync nounwind willreturn
declare void @llvm.lifetime.end.p0i8(i64 immarg, i8* nocapture) #1

attributes #0 = { nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { argmemonly nofree nosync nounwind willreturn }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2}
!llvm.ident = !{!3}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 7, !"uwtable", i32 1}
!2 = !{i32 7, !"frame-pointer", i32 2}
!3 = !{!"clang version 14.0.0"}
!4 = !{i64 2147613314}
!5 = !{i64 2147613405}
