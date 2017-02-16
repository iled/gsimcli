# gsimcli:
Geostatistical SIMulation for the homogenisation and interpolation of
CLImate data

[![Documentation Status](https://readthedocs.org/projects/gsimcli/badge/?version=latest)](http://gsimcli.readthedocs.org/en/latest/?badge=latest) [![Documentation Status](https://readthedocs.org/projects/gsimcli/badge/?version=dev)](http://gsimcli.readthedocs.org/en/latest/?badge=dev) [![Code Issues](https://www.quantifiedcode.com/api/v1/project/d5107719f2724f41bc1b18665a164616/snapshot/origin:dev:HEAD/badge.svg)](https://www.quantifiedcode.com/app/project/d5107719f2724f41bc1b18665a164616)

## What is it

**gsimcli** is a method to homogenise climate data using
geostatistical stochastic simulation methods.

It is presented here as an open source Python project. Some of its
modules are intended to serve as useful libraries for other projects.

## Development

**gsimcli** is implemented using **Direct Sequential
Simulation** (DSS) [[1]](#ref1). The method description and its application have already
been published [[2]](#ref2).

This research project is hosted at [NOVA IMS](http://www.novaims.unl.pt)
(Lisbon, Portugal) and it is funded by the "Fundação para a Ciência e
Tecnologia" ([FCT](http://www.fct.pt)), Portugal, through the research project
PTDC/GEO-MET/4026/2012. See the [approval and funding notice](http://www.novaims.unl.pt/documentos/P_GSIMCLI_EN.pdf).

The outcomes of this project also include three peer-reviewed papers published in
scientific journals. See the complete list of the [Project Publications](#publications)
below.

### Note by the programmer

This software is no longer being developed. Of course, development may continue
in any fork.

The latest and last version is available in the `master` branch.

The [Issues](https://github.com/iled/gsimcli/issues) page lists the tasks and
ideas that were not implemented and/or completed, as well as known limitations.
Those may be a source of ideas for any eventual future development.

![NOVA IMS](/images/IMS_Preto_logo.png) ![FCT](/images/logo_FCT.png)

## Documentation

The documentation (user manual) is hosted at readthedocs.org:
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

<a name="ref1"></a>[1]: Soares, Amílcar. *Direct Sequential Simulation and Cosimulation.*
Mathematical Geology 33, no. 8 (2001): 911-926.
http://link.springer.com/article/10.1023/A:1012246006212.

<a name="ref2"></a>[2]: Costa, AC, and A Soares. *Homogenization of Climate Data: Review and New
Perspectives Using Geostatistics.* Mathematical Geosciences 41, no. 3 (November
28, 2009): 291-305. doi:10.1007/s11004-008-9203-3.


## <a name="publications"></a>Project Publications

### Scientific Journals

Ribeiro, S., Caineta, J., Costa, A. C., Henriques, R. (2016) [gsimcli: a geostatistical procedure for the homogenisation of climatic time series](http://doi.org/10.1002/joc.4929). International Journal of Climatology. doi: 10.1002/joc.4929

Ribeiro, S., Caineta, J., Costa, A. C., Henriques, R., Soares, A. (2016) [Detection of inhomogeneities in precipitation time series in Portugal using direct sequential simulation](http://doi.org/10.1016/j.atmosres.2015.11.014). Atmospheric Research 171, 147–158. doi: 10.1016/j.atmosres.2015.11.014

Ribeiro, S., Caineta, J., Costa, A. C., (2015) [Review and discussion of homogenisation methods for climate data.](http://doi.org/10.1016/j.pce.2015.08.007). Physics and Chemistry of the Earth 94, 167 - 179. doi: 10.1016/j.pce.2015.08.007

### Proceedings

Ribeiro, S., Caineta, J., Costa, A. C., Soares, A. (2015). [Establishment of detection and correction parameters for a geostatistical homogenisation approach](http://doi.org/10.1016/j.proenv.2015.07.115). Procedia Environmental Sciences, 27, 83-88. doi: 10.1016/j.proenv.2015.07.115

Caineta, J., Ribeiro, S., Soares, A., Costa, A. C. (2015). [Workflow for the homogenisation of climate data using geostatistical simulation](http://sgem.org/sgemlib/spip.php?article5707). In: Conference Proceedings of the 15th SGEM GeoConference on Informatics, Geoinformatics and Remote Sensing. Albena, Bulgaria, 16-25 June 2015, Vol. 1, pp. 921-929.

Ribeiro, S., Caineta, J., Costa, A. C., Henriques, R. (2015). [Analysing the detection and correction parameters in the homogenisation of climate data series using gsimcli](https://agile-online.org/Conference_Paper/cds/agile_2015/shortpapers/59/59_Paper_in_PDF.pdf ). In: F. Bacao, M. Y. Santos, M. Painho (Eds.), The 18th AGILE International Conference on Geographic Information Science, Lisbon, Portugal, 9-12 June 2015.

Caineta, J., Ribeiro, S., Henriques, R., Costa, A. C. (2015). [A Package for the homogenisation of climate data using geostatistical simulation](https://www.thinkmind.org/index.php?view=article&articleid=geoprocessing_2015_6_40_30130). In: GEOProcessing 2015: The Seventh International Conference on Advanced Geographic Information Systems, Applications, and Services, Lisbon, Portugal, 22-27 February 2015.

### Other Publications

Caineta, J., Ribeiro, S., Henriques, R., Soares, A., Costa, A. C. (2014). [Benchmarking a geostatistical procedure for the homogenisation of annual precipitation series](http://meetingorganizer.copernicus.org/EGU2014/EGU2014-7605.pdf). In: Geophysical Research Abstracts, Vol. 16, EGU2014-7605, European Geosciences Union General Assembly 2014. (Vienna, Austria, 27 April –2 May 2014)

Caineta, J., Ribeiro, S., Costa, A. C., Henriques, R., Soares, A. (2014). [Inhomogeneities detection in annual precipitation time series in Portugal using direct sequential simulation](http://meetingorganizer.copernicus.org/EGU2014/EGU2014-7849.pdf). In: Geophysical Research Abstracts, Vol. 16, EGU2014-7849, European Geosciences Union General Assembly 2014. (Vienna, Austria, 27 April –2 May 2014)

Ribeiro, S., Caineta, J., Henriques, R., Soares, A., Costa, A. C. (2014). [Advantages and applicability of commonly used homogenisation methods for climate data](http://meetingorganizer.copernicus.org/EGU2014/EGU2014-7725.pdf). In: Geophysical Research Abstracts, Vol. 16, EGU2014-7725, European Geosciences Union General Assembly 2014. (Vienna, Austria, 27 April –2 May 2014)
