# Future 和 await 说明

本文档记录 FRLanguage 第一版 Future 的设计和当前支持范围。

## 目标

第一版 Future 的目标是学习异步模型的基本结构，而不是实现真正并发。

当前支持：

- `future { ... }`
- `await`
- 函数返回 Future
- Future 成功完成
- Future 失败传播

## 基本用法

```fr
let value = await future {
  return 42;
};

print(value);
```

输出：

```txt
42
```

## 函数返回 Future

```fr
fn later(x) {
  return future {
    return x + 1;
  };
}

print(await later(41));
```

输出：

```txt
42
```

## 当前执行模型

当前 `future { ... }` 不会在创建时立即执行，而是会被放入 Runtime 的任务队列。

流程：

```txt
future 块 -> 创建 Future -> 加入任务队列 -> await 时运行任务 -> 捕获 return -> resolve Future
```

如果 future 块中没有 `return`，Future 的完成值是 `nil`。

如果 future 块中出现运行时错误，Future 会进入失败状态；后续 `await` 这个 Future 时会抛出错误。

示例：

```fr
let value = future {
  print("future");
  return 42;
};

print("before");
print(await value);
```

输出：

```txt
before
future
42
```

## await 规则

`await` 只能用于 Future。

合法：

```fr
await future {
  return 1;
}
```

非法：

```fr
await 1
```

会报运行时错误：

```txt
await 只能用于 Future
```

## 和真正异步的区别

当前 Future 不是并发执行，但已经有一个最小任务队列。

也就是说，这一版先完成：

```txt
Future 对象
future 语法
await 语法
任务队列
await 时驱动调度器
成功值传递
错误传递
```

后续可以再扩展：

```txt
pending 状态等待
异步恢复
真正 IO 异步
```
