#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int system(const char *command);

void main(int argc, char *argv[])
{
    if (argc < 2)
    {
        printf("Usage: run <in.bfasm> [<args>]\n");
        exit(1);
    }
    char str1[100] = "python3 assemble.py ";
    char *str2 = argv[1];
    char str3[] = " run.bf";
    strcat(str1, str2);
    strcat(str1, str3);
    if (system(str1) != 0) {
        printf("Could not assemble file\n");
        exit(1);
    }
    if (system("python3 compileToPython.py run.bf run.bfpy") != 0) {
        printf("Could not compile file\n");
        exit(1);
    }
    printf("running\n========================\n");
    system("python3 run.bfpy");
}
