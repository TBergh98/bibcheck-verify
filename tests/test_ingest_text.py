from bibcheck.ingest.text import parse_text


def test_text_parser_preserves_doi_text_for_llm_extraction():
	text = """References:

Cook, J.K.A., Jackwood, M., Jones, R.C., 2012. The long view. https://doi.org/10.1080/ 03079457.2012.680432.
Houadfi, M., Ennaji, M.M., 2015. Phylogenetic analysis. https://doi.org/10.1186/s12985-015-0347- 8.
Huo, J.L., Wu, G.S., 2014. Genetic diversity. https://doi.org/10.4238/2014 April.29.16.
Wang, R., Yang, L., Xiang, B., 2024. Genetic characterization. [https://doi.org/10.1016/j.psj.2024.104040](https://doi.org/10.1016/j.psj.2024.104040). 9 W. Mu et al.
Chen, H., Shi, W., Feng, S., 2024. A novel virus. [https://doi.org/10.1016/j.psj.2024.103881](https://doi.org/10.1016/j.psj.2024.103881). Chen, X., Mu, W.
Liu, L., Li, B., Yu, L., 2020. Complete genome sequencing. https://doi/. org/10.3390/v12040366.
H., 2019. Glycosylation of the viral attachment protein. https:// doi.org/10.1074/jbc.RA119.007532.
C., Mundt, E., 2018. Recombinant vaccines. https:// doi.org/10.1016/j.vaccine.2018.01.017.
"""

	references = parse_text(text)

	assert len(references) == 8
	assert all(reference.doi_if_present is None for reference in references)
	assert "10.1080/ 03079457.2012.680432" in references[0].raw_text


