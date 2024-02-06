This repository contains supplemental material to the article 
"Finding hardness reductions automatically using SAT solvers"
by Helena Bergold, Manfred Scheucher, and Felix Schröder





## Installation

To run the framework pysat needs to be installed, see https://pysathq.github.io/installation/

Optional: 
To verify unsatisfiability,
install cadical https://github.com/arminbiere/cadical
and drat-trim https://github.com/marijnheule/drat-trim

Optional: 
To verify that settings are non-isomorphic,
install KCBox https://github.com/meelgroup/KCBox



## Enumerating the settings

The following command performs the enumeration of all 
families $\mathcal{F}$ of rank 3 sign patterns on $[4]$
with $`\mathcal{F} \subseteq \{+-+-,+--+,+---,-+-+,-+--,--+-,---+,----\}`$
and writes all settings to the file `r3_settings.txt`.
Each line in the file encodes a setting.
```
    python enum_settings.py 3 > r3_settings.txt
```
Since among the $256 = 2^8$ subsets there are some symmetries,
our program filters out 144 that are lexicographically minimal
with respect to 

- inverting signs (i.e., changing $+$ to $-$ and vice versa) and
- reversing the elements $`\{1,\ldots,n\}`$ to $`\{n,\ldots,1\}`$.

Note that there might be other symmetries among the classes.

Similarly, one can enumerate all settings for rank 4 using
```
    python enum_settings.py 4 > r4_settings.txt
```
Note that this will take several cpu days.
The benchmark selection, however, can be enumerated almost instantly using 
```
    python enum_settings.py 4 --selection > r4_settings_selection.txt
```


## Duplicate checking

To check whether a file only contains non-isomorphic settings,
we provide a script `count_configurations.py`
which uses a model counting implementation from KCBox 
to count all configurations up to a certain number of elements $n$ for each setting.
To verify that the 41 settings in `r3_settings_hard.txt` are non-isomorphic, 
it is sufficient to use $n=6$ as all settings yield different numbers:
```
python count_configurations.py r3_settings_hard.txt 3 6
```


## Testing completability

The script loads settings from an input file
and for each setting it searches gadgets for the reduction. 
If the script terminates unsuccessfully for a setting, 
then there are no gadget of the specified size.
If the script finds enough gadgets for a reduction, 
it creates a certificate in the `certificates_r{rank}_{algorithm}/` folder
which verifies that the setting NP-hard.
By re-running the script, an existing certificate will be reloaded and verified to save time.


For example, the following command searches gadgets of size 5 
for all rank 3 settings encoded in the file `r3_settings_all.txt`:
```
    python find_gadgets.py r3_settings_all.txt 3 5
```
As outlined in our paper, the computation only takes a few CPU minutes on a single CPU
to classify 31 of the 144 settings as hard.
To search all structures for gadgets of size 6 in the remaining settings, 
we used the computing cluster at TU Berlin.
Even though finding gadgets is a non-trivial task, 
pre-computed gadgets can be verified within a few seconds with by following command:
```
    python find_gadgets.py r3_settings_all.txt 3 6 --load -cp certificates_r3/ --verifyonly
```
Our certificates are provided in `certificates_r3.tar.gz` and `certificates_r4.tar.gz`.

To exclude errors from the SAT solver, one can also run
```
    python find_gadgets.py r3_settings_all.txt 3 6 --load -cp certificates_r3/ --verifyonly --verifydrat
```
This will check the correctness of a model in the case a CNF is satisfiable,
and otherwise, if the CNF is unsatisfiablitiy,
it will use cadidal to create a DRAT certificate and 
employ the independent proof-checking tool DRAT-trim to verify the certificate.


## Certificates

A certificate is text file which encodes a python dictionary with the following entries:

- `n` encodes the size of the gadget.

- `fpatterns` encodes the setting as a list of forbidden patterns, e.g., `['+-+-', '-+-+']`.

- `pgadgets` holds a sub-dictionary which encodes up to 4 propagator gadgets.
The keys are strings such as `'A or not B'` and encode
the Boolean formulas corresponding to the gadgets.

- `cgadgets` holds a sub-dictionary which encodes up to 8 clause gadgets. 
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
{
    'n': 5,
    'fpatterns': ['+-+-', '-+-+'], 
    `pgadgets`: {
        'A or B': (5, '??++-?+?+?', ((0, 1, 2), (2, 3, 4))), 
        'A or not B': (4, '?+-?', ((0, 1, 2), (1, 2, 3))), 
        'not A or B': (4, '?-+?', ((0, 1, 2), (1, 2, 3))), 
        'not A or not B': (5, '??-++?-?-?', ((0, 1, 2), (2, 3, 4)))
    }, 
    `cgadgets`: {
        'A or not B or C': (5, '??+--???+?', ((0, 1, 2), (1, 2, 3), (2, 3, 4)))
    }
}
```
