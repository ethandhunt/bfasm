.bfasm
    methods:
        declare a func by prefacing it with '.'
        declare a multiFunc by prefacing it with '-'
        args are prefaced with '%'
        
        func:
            declaration:
                |.funcName %arg1 %arg2 ... %argN
                |    ; code

            call:
                |.start
                |    .funcName "12N"

            compile path:
                in: .start

                line: .funcName "12N"
                parsedLine: ['.funcName', 49, 50, 78]

                enterFunc('funcName', [49, 50, 78])

            number of args must match number of args in declaration

        multiFunc:
            declaration:
                |-funcName %arg1
                |    ; code

            call:
                |.start
                |    .funcName "12N"

            compile path:
                in         .start:
                            ^
                line:       .funcName "12N"
                parsedLine: ['.funcName', 49, 50, 78]

                enterFunc('.funcName', [49])
                enterFunc('.funcName', [50])
                enterFunc('.funcName', [78])

            number of args must be divisible by number of args in declaration
