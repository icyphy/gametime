import re

llvm_ir_string = "{%0:\\l  %1 = alloca i32, align 4\\l  %2 = alloca i32, align 4\\l  %3 = alloca i32, align 4\\l  %4 = alloca i32, align 4\\l  store i32 0, i32* %1, align 4\\l  call void @llvm.dbg.declare(metadata i32* %2, metadata !13, metadata\\l... !DIExpression()), !dbg !19\\l  store i32 1, i32* %2, align 4, !dbg !19\\l  %5 = load i32, i32* %2, align 4, !dbg !20\\l  %6 = call i32 (i8*, ...) @printf_(i8* getelementptr inbounds ([9 x i8], [9 x\\l... i8]* @.str, i32 0, i32 0), i32 %5), !dbg !21\\l  call void @llvm.dbg.declare(metadata i32* %3, metadata !22, metadata\\l... !DIExpression()), !dbg !23\\l  store i32 2, i32* %3, align 4, !dbg !23\\l  %7 = load i32, i32* %3, align 4, !dbg !24\\l  %8 = call i32 (i8*, ...) @printf_(i8* getelementptr inbounds ([9 x i8], [9 x\\l... i8]* @.str.1, i32 0, i32 0), i32 %7), !dbg !25\\l  call void @llvm.dbg.declare(metadata i32* %4, metadata !26, metadata\\l... !DIExpression()), !dbg !27\\l  %9 = load i32, i32* %2, align 4, !dbg !28\\l  %10 = load i32, i32* %3, align 4, !dbg !29\\l  %11 = call i32 @add(i32 %9, i32 %10), !dbg !30\\l  store i32 %11, i32* %4, align 4, !dbg !27\\l  %12 = load i32, i32* %4, align 4, !dbg !31\\l  %13 = call i32 (i8*, ...) @printf_(i8* getelementptr inbounds ([9 x i8], [9\\l... x i8]* @.str.2, i32 0, i32 0), i32 %12), !dbg !32\\l  %14 = load i32, i32* %4, align 4, !dbg !33\\l  %15 = icmp eq i32 %14, 3, !dbg !35\\l  br i1 %15, label %16, label %18, !dbg !36\\l|{<s0>T|<s1>F}}', '{%16:\\l16:                                               \\l  %17 = call i32 (i8*, ...) @printf_(i8* getelementptr inbounds ([5 x i8], [5\\l... x i8]* @.str.3, i32 0, i32 0)), !dbg !37\\l  store i32 0, i32* %1, align 4, !dbg !39\\l  br label %20, !dbg !39\\l}', '{%20:\\l20:                                               \\l  %21 = load i32, i32* %1, align 4, !dbg !43\\l  ret i32 %21, !dbg !43\\l}"

# Use regular expression to find the labels
labels = re.findall(r'%(\d+):', llvm_ir_string)

# Convert labels to integers and store them in a list
labels_list = [int(label) for label in labels]

print(labels_list)
