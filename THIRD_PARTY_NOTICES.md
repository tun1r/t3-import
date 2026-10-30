# Third-party notices

## T3 Code

`patches/stable-session-import.patch` contains changes to
[T3 Code](https://github.com/pingdotgg/t3code), including portions of its source.
The upstream license is reproduced below.

MIT License

Copyright (c) 2026 T3 Tools Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## CarlosGtrz/t3-import

Claude conversation-branch selection and compaction handling in
`patches/stable-session-import.patch` were implemented with reference to the Claude
parser in [CarlosGtrz/t3-import](https://github.com/CarlosGtrz/t3-import).
Credit goes to CarlosGtrz and the t3-import contributors for that earlier work.
The implementation here integrates those behaviors with T3's v2 scanner and import
service.

Reference source:
[`src/sources/claude.ts` at `5e20fb5709aa7ad6ce0853e210426c551066d7e0`](https://github.com/CarlosGtrz/t3-import/blob/5e20fb5709aa7ad6ce0853e210426c551066d7e0/src/sources/claude.ts).
Its [license](https://github.com/CarlosGtrz/t3-import/blob/5e20fb5709aa7ad6ce0853e210426c551066d7e0/LICENSE)
is reproduced below.

MIT License

Copyright (c) 2026 t3-import contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
