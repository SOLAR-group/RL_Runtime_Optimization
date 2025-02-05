#!/bin/sh

MROOT=.. CFLAGS="-fpermissive --coverage -g -O0" LFLAGS="-lgcov" make -C simp
