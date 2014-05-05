# gsimcli:
**G**eostatistical **sim**ulation for the homogenisation and interpolation of
**cli**mate data

## What is it

**gsimcli** is a proposed method to homogenise climate data using
geostatistical stochastic simulation methods.

It is presented here as a *work on progress* Python project. Some of its
modules are intended to serve as useful libraries for other projects.

## Development

In a first stage, **gsimcli** will be implemented using **Direct Sequential
Simulation** (DSS)[1]. Method description and application have already been
published [2].

It is planned to develop an implementation using Direct Sequential Simulation
with **local distributions**.

This research project is hosted at [ISEGI-NOVA](http://www.isegi.unl.pt)
(Lisbon, Portugal) and it is funded by the "Fundação para a Ciência e
Tecnologia" ([FCT](http://www.fct.pt)), Portugal, through the research project
PTDC/GEO-MET/4026/2012. See [approval and funding notice]
(http://www.isegi.unl.pt/documentos/P_GSIMCLI_EN.pdf).

![ISEGI-NOVA](/images/logo_ISEGI.png) ![FCT](/images/logo_FCT.png)

## Documentation

The Sphinx documentation is hosted at readthedocs.org:
http://gsimcli.readthedocs.org

Browse and post issues and contributions [here]
(https://github.com/iled/gsimcli/issues).

## Dependencies

- [NumPy](http://www.numpy.org): 1.8 or higher
- [pandas](http://pandas.pydata.org) 0.13.0 or higher
- [DSS](https://sites.google.com/site/cmrpsoftware/geoms) only the binary
- [Wine](http://www.winehq.org) only for *nix systems

## License

GPLv3

## References

[1]: Soares, Amílcar. “Direct Sequential Simulation and Cosimulation.”
Mathematical Geology 33, no. 8 (2001): 911–926.
http://link.springer.com/article/10.1023/A:1012246006212.

[2]: Costa, AC, and A Soares. “Homogenization of Climate Data: Review and New
Perspectives Using Geostatistics.” Mathematical Geosciences 41, no. 3 (November
28, 2009): 291–305. doi:10.1007/s11004-008-9203-3.
