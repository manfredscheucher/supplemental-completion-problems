This repository contains supplemental material to the article 
"Using SAT to find NP-hardness proofs for 41 completion problems"
by Helena Bergold, Manfred Scheucher, and Felix Schröder





## Installation

To run the framework pysat needs to be installed, see https://pysathq.github.io/installation/

Optional: To verify unsatisfiability,
install cadical https://github.com/arminbiere/cadical
and drat-trim https://github.com/marijnheule/drat-trim




## Enumerating the settings

The following command performs the enumeration of all families $\mathcal{F}$ of rank 3 sign patterns on $[4]$
with $`\mathcal{F} \subseteq \{+-+-,+--+,+---,-+-+,-+--,--+-,---+,----\}`$
and writes all settings to the file `settings.txt`.
Each line in the file encodes a setting.
```
    python enum_settings.py > settings.txt
```
Since among the $256 = 2^8$ subsets there are some symmetries,
our program filters out 144 that are lexicographically minimal
with respect to 

- inverting signs (i.e., changing $+$ to $-$ and vice versa) and
- reversing the elements $`\{1,\ldots,n\}`$ to $`\{n,\ldots,1\}`$.

Note that there might be other symmetries among the classes.




## Duplicate checking

To verify that all 144 settings are non-isomorphic,
we provide a script `enumerate.py` which enumerates all configurations up to a certain number of elements $n$ for a list of settings.
```
    python enumerate.py settings.txt --countonly --nozeros 5 --fp_dup dup5.txt
    python enumerate.py dup5.txt --countonly --nozeros 6 --fp_dup dup6.txt
    python enumerate.py dup6.txt --countonly --table 4
```
First, the number of all configurations for up to $n=5$ is computed and settings yielding duplicate sequences are written to the file `dup5.txt`.
For those settings, we next computed all numbers for up to $n=6$ and again output settings which yield duplicate sequences to the file `dup6.txt`.
However, when counting all partial configurations
and distinguishing those with distinct numbers of zeros
(which is done by the `--table` parameter),
all settings yield different numbers.


## Testing completability

The script loads settings from an input file
and for each setting it searches gadgets for the reduction. If the script terminates unsuccessfully for a setting, then there are no gadget of the specified size.
If the script finds enough gadgets for a reduction, it creates a certificate in the `certificates/` folder
which verifies that the setting NP-hard.
By re-running the script, an existing certificate will be reloaded and verified to save time.


For example, the following command searches gadgets of size 5 for all settings encoded in the file `settings.txt`:
```
    python find_gadgets.py settings.txt 5
```
Even when removing existing certificates, 
its computation time is only about 10 CPU minutes.
To search all structures for gadgets of size 6 in the remaining settings, 
we used the computing cluster at TU Berlin. 
Even though finding gadgets is a non-trivial task, 
all found gadgets for the 41 settings
can be verified within a few seconds with by following command:
```
    python find_gadgets.py settings_hard.txt 6 --verifyonly
```



## Certificates

A certificate consists of the following triple:

- The setting is encoded by a list of forbidden patterns, e.g., `['+-+-', '-+-+']`.

- A dictionary of up to 4 propagator gadgets.
The keys are strings such as `'A or not B'` and encode
the Boolean formulas corresponding to the gadgets.

- A dictionary of up to 8 clause gadgets. 
The keys are strings such as `'A or not B or C'` and encode
the Boolean formulas corresponding to the gadgets.


Each gadgets is encoded by the triple:

- Size of the gadgets as integer.
Note that, in our python code, 
sign mappings are on the elements $`\{0,\ldots,n-1\}`$.

- The sign mapping encoded as string. 
For example, `?+-?` encodes the mapping
$\sigma(013)=+,\sigma(023)=-$ on the elements $`\{0,1,2,3\}`$.

- The location of the variables in the gadget.
For example `(0, 1, 2), (1, 2, 3)` encodes that the first variable $A$ is encoded in the triple $(0, 1, 2)$ and the second variable $B$ is encoded in the triple $(1, 2, 3)$.


To give a concrete example:
the NP-hardness certificate for the setting of generalized signotopes (i.e., $`\mathcal{F} = \{+-+-,-+-+\}`$) looks as follows:
```
(
    ['+-+-', '-+-+'], 
    {
        'A or B': (5, '??++-?+?+?', ((0, 1, 2), (2, 3, 4))), 
        'A or not B': (4, '?+-?', ((0, 1, 2), (1, 2, 3))), 
        'not A or B': (4, '?-+?', ((0, 1, 2), (1, 2, 3))), 
        'not A or not B': (5, '??-++?-?-?', ((0, 1, 2), (2, 3, 4)))
    }, 
    {
        'A or not B or C': (5, '??+--???+?', ((0, 1, 2), (1, 2, 3), (2, 3, 4)))
    }
)
```
