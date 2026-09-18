# ImmGen GSE109125 Default Expression Resource

The NeKo `find_immgen_genes` tool downloads the normalized gene-count table for
ImmGen series GSE109125 to this directory when `IMMGEN_DATA_PATH` is not set and
the local cache is absent.

- Dataset: ImmGen ULI RNA-seq compendium, GSE109125
- Source: https://sharehost.hms.harvard.edu/immgen/GSE109125/GSE109125_Normalized_Gene_count_table.csv
- Catalog: https://rstats.immgen.org/DataPage/
- File: `GSE109125_Normalized_Gene_count_table.csv`

The table contains gene symbols as rows and normalized expression values for
individual ImmGen samples as columns. To query a population, use its shared
column-name prefix, excluding the replicate suffix. For example, `T.4.Nve`
selects naive CD4 T-cell sample columns.

The data are an ImmGen public resource. Users must comply with the applicable
ImmGen and GEO terms and cite the dataset in downstream scientific work.