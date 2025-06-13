Great! Let's start with **Python basic and intermediate tricky interview questions** that test both **conceptual understanding** and **coding skills**. These include **programming challenges, tricky outputs, and debugging scenarios**.

---

## **Basic Tricky Python Interview Questions**
These focus on **edge cases, memory handling, Python internals, and tricky syntax behavior**.

### **1. Mutable vs. Immutable Objects**
**Q1: What will be the output of the following code?**
```python
def modify_list(lst):
    lst.append(4)

my_list = [1, 2, 3]
modify_list(my_list)
print(my_list)
```
- **Expected Answer:** `[1, 2, 3, 4]`
- **Concept Tested:** Lists are **mutable**, so modifications inside functions persist.

---

**Q2: What will be the output of the following code?**
```python
def modify_string(s):
    s = s + " world"
    return s

string1 = "hello"
modify_string(string1)
print(string1)
```
- **Expected Answer:** `"hello"`
- **Concept Tested:** Strings are **immutable**, so `s` inside `modify_string` is a new object.

---

### **2. Unexpected Integer Division**
**Q3: What will be the output of this code?**
```python
print(3 * 3 ** 3)
print(2 ** 2 ** 3)
```
- **Expected Answer:**  
  - `3 * 3 ** 3 → 3 * (3^3) = 3 * 27 = 81`
  - `2 ** 2 ** 3 → 2 ** (2^3) = 2 ** 8 = 256`
- **Concept Tested:** Exponentiation (`**`) is **right associative**.

---

### **3. Mutable Default Arguments**
**Q4: What will be the output of this code?**
```python
def add_to_list(value, my_list=[]):
    my_list.append(value)
    return my_list

print(add_to_list(1))
print(add_to_list(2))
print(add_to_list(3, []))
```
- **Expected Answer:**  
  - `[1]`
  - `[1, 2]`
  - `[3]`
- **Concept Tested:** Default mutable arguments **persist across function calls**.

---

### **4. The Unexpected Tuple**
**Q5: What will be the output of the following?**
```python
t = (1, 2, 3)
t[1] = 4
print(t)
```
- **Expected Answer:**  
  - **Error** (`TypeError: 'tuple' object does not support item assignment`)
- **Concept Tested:** Tuples are **immutable**, so elements cannot be reassigned.

---

### **5. Function Arguments - Positional vs. Keyword**
**Q6: What will be the output of the following?**
```python
def func(a, b=10, c=20):
    print(a, b, c)

func(1, c=5)
```
- **Expected Answer:** `1 10 5`
- **Concept Tested:**  
  - **Positional arguments come first.**
  - **Keyword arguments override default values.**

---

## **Intermediate Tricky Python Interview Questions**
These cover **decorators, lambdas, comprehensions, recursion, and multi-threading.**

### **6. Lambda in a Loop**
**Q7: What will be the output of the following?**
```python
funcs = [lambda x: x + i for i in range(3)]
print([f(0) for f in funcs])
```
- **Expected Answer:** `[2, 2, 2]`
- **Concept Tested:**  
  - **Late binding in lambdas** (`i` is evaluated at execution time, not when created).

---

### **7. Dictionary Key Ordering**
**Q8: What will be the output?**
```python
d = {1: "one", True: "True", 1.0: "float"}
print(d)
```
- **Expected Answer:** `{1: "float"}`
- **Concept Tested:**  
  - `1`, `True`, and `1.0` are treated as the **same dictionary key**.

---

### **8. List Comprehension with Condition**
**Q9: What will be the output?**
```python
numbers = [1, 2, 3, 4]
new_numbers = [x for x in numbers if x % 2 == 0 if x > 2]
print(new_numbers)
```
- **Expected Answer:** `[4]`
- **Concept Tested:**  
  - **Multiple conditions in list comprehensions.**

---

### **9. Function Closure - Nested Function**
**Q10: What will be printed?**
```python
def outer(x):
    def inner(y):
        return x + y
    return inner

fn = outer(10)
print(fn(5))
```
- **Expected Answer:** `15`
- **Concept Tested:**  
  - **Closures** (inner functions retain the value of `x` from `outer`).

---

### **10. Threading vs. Multiprocessing**
**Q11: What will be printed?**
```python
import threading

count = 0
def increment():
    global count
    for _ in range(1000000):
        count += 1

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)

t1.start()
t2.start()

t1.join()
t2.join()

print(count)
```
- **Expected Answer:** **Not necessarily 2,000,000!** (Due to race conditions)
- **Concept Tested:**  
  - **Thread safety issues** (GIL does not protect against race conditions in global variables).

---

## **Challenge Problem**
### **12. Recursive Fibonacci**
**Q12: Write a recursive function to calculate the nth Fibonacci number. Optimize it using memoization.**

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(10))
```
- **Concept Tested:**  
  - **Recursion and memoization (`lru_cache`).**
  - **Optimization in large calculations.**

---

## **13. Tricky Sorting Question**
**Q13: How would you sort this list by the second letter of each string?**
```python
words = ["banana", "apple", "cherry"]
sorted_words = sorted(words, key=lambda x: x[1])
print(sorted_words)
```
- **Expected Answer:** `['banana', 'apple', 'cherry']`
- **Concept Tested:**  
  - **Custom sorting with lambdas.**

---

## **14. Tricky Exception Handling**
**Q14: What happens if you run this?**
```python
try:
    print(1 / 0)
except ZeroDivisionError as e:
    print("Error:", e)
finally:
    print("Finally block executed.")
```
- **Expected Answer:**  
  ```
  Error: division by zero
  Finally block executed.
  ```
- **Concept Tested:**  
  - `finally` always **executes**, even after exceptions.

---

## **Conclusion**
These questions **test real-world coding scenarios** while also exploring **Python internals and tricky behaviors**. 

✅ Next Steps: Do you want **harder advanced Python coding problems** or should we move to **SQL next**? 🚀