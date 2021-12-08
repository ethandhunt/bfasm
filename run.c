#include <stdlib.h>
#include <string.h>
#include <stdio.h>

int system(const char *command);

void main(int argc, char *argv[])
{
    if (argc < 2)
    {
        printf("Usage: run <in.bf> [<args>]\n");
        exit(1);
    }
    char str1[100] = "python3 compileToPython.py ";
    char *str2 = argv[1];
    char str3[] = " run.bfpy";
    strcat(str1, str2);
    strcat(str1, str3);
    if (system(str1) != 0) {
        printf("Error: Compilation failed\n");
        exit(1);
    }
    printf("running\n========================\n");
    system("python3 run.bfpy");
}
