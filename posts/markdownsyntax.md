---
title: 'Syntax highlighting in markdown'
date: '12-07-2024'
---

## Syntax Highlighting in Markdown

I am trying to use the remark library to highlight syntax but to no avail

<code>This is supposed to be a code snippet</code>

And this is supposed to be a code block

```bash
echo "Hello World"
```

```python
print("Hello World")
```

Yet, the libraries I find are deprecated or not working. I am at a loss.
I will update this post when I find a solution.

### Other features to add to this blog
- Add a search bar
- Add a comment section using Github [Utterances](https://github.com/utterance/utterances "Visit Utterances!")
- make sure this `code here` works.
## special symbol test
- `&` &amp;
- `>` &gt;
- `<` &lt;
- `"` &quot;
- `'` &apos;
- `©` &copy;
- `®` &reg;
- `™` &trade;
- `€` &euro;
- `£` &pound;
- `¥` &yen;
- `¢` &cent;
- `§` &sect;
- `¶` &para;

## Trying out a huge program

```python
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

n = 10
for i in range(n):
    print(fibonacci(i))
```




