# gsimcli:
Geostatistical SIMulation for the homogenisation and interpolation of
CLImate data

[![Documentation Status](https://readthedocs.org/projects/gsimcli/badge/?version=latest)](http://gsimcli.readthedocs.org/en/latest) [![Documentation Status](https://readthedocs.org/projects/gsimcli/badge/?version=dev)](http://gsimcli.readthedocs.org/en/dev) [![Code Issues](https://www.quantifiedcode.com/api/v1/project/d5107719f2724f41bc1b18665a164616/snapshot/origin:dev:HEAD/badge.svg)](https://www.quantifiedcode.com/app/project/d5107719f2724f41bc1b18665a164616)

## What is it

**gsimcli** is a proposed method to homogenise climate data using
geostatistical stochastic simulation methods.

It is presented here as an open source Python project. Some of its
modules are intended to serve as useful libraries for other projects.

## Development

**gsimcli** is implemented using **Direct Sequential
Simulation** (DSS) [1]. The method description and its application have already
been published [2].

This research project is hosted at [NOVA IMS](http://www.novaims.unl.pt)
(Lisbon, Portugal) and it is funded by the "Fundação para a Ciência e
Tecnologia" ([FCT](http://www.fct.pt)), Portugal, through the research project
PTDC/GEO-MET/4026/2012. See [approval and funding notice]
(http://www.novaims.unl.pt/documentos/P_GSIMCLI_EN.pdf).

![NOVA IMS](/images/IMS_Preto_logo.png) ![FCT](/images/logo_FCT.png)

## Documentation

The documentation is hosted at readthedocs.org:
http://gsimcli.readthedocs.org

Browse and post issues and contributions [here]
(https://github.com/iled/gsimcli/issues).

## Dependencies

- [Python](http://www.python.org): 2.7
- [NumPy](http://www.numpy.org): 1.8 or higher
- [pandas](http://pandas.pydata.org) 0.17.1 or higher
- [DSS](https://sites.google.com/site/cmrpsoftware/downloads) only the binary (*newDSSintelRelease*)
- [Wine](http://www.winehq.org) only for *nix systems
- See [requirements.txt](requirements.txt) for the complete list of dependencies

## License

GPLv3

## References

[1]: Soares, Amílcar. *Direct Sequential Simulation and Cosimulation.*
Mathematical Geology 33, no. 8 (2001): 911-926.
http://link.springer.com/article/10.1023/A:1012246006212.

[2]: Costa, AC, and A Soares. *Homogenization of Climate Data: Review and New
Perspectives Using Geostatistics.* Mathematical Geosciences 41, no. 3 (November
28, 2009): 291-305. doi:10.1007/s11004-008-9203-3.
