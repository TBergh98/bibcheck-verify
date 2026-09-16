from pathlib import Path

from bibcheck.ingest.text import parse_text


def test_reference_fixture_does_not_collapse_to_a_handful_of_entries():
	references = parse_text(Path("input_test/test.md"))

	assert len(references) == 44
	bali = next(reference for reference in references if "10.3390/v13040535" in reference.raw_text)
	marandino = next(reference for reference in references if "10.3390/v14102095" in reference.raw_text)
	assert "Banyai, K." in bali.raw_text
	assert "Williman, J." in marandino.raw_text
	assert "South America. Viruses 14, 2095." in marandino.raw_text


def test_doi_extraction_ignores_spaces_inside_doi():
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

	assert references[0].doi_if_present == "10.1080/03079457.2012.680432"
	assert references[1].doi_if_present == "10.1186/s12985-015-0347-8"
	assert references[2].doi_if_present == "10.4238/2014april.29.16"
	assert references[3].doi_if_present == "10.1016/j.psj.2024.104040"
	assert references[4].doi_if_present == "10.1016/j.psj.2024.103881"
	assert references[5].doi_if_present == "10.3390/v12040366"
	assert references[6].doi_if_present == "10.1074/jbc.ra119.007532"
	assert references[7].doi_if_present == "10.1016/j.vaccine.2018.01.017"


def test_numbered_references_without_doi_are_split():
	references = parse_text(Path("input_test/test_poultry.md"))

	assert len(references) == 26
	assert "Transitioning towards Cage-Free Farming" in references[0].raw_text
	assert "Welfare Quality® Assessment Protocol" in references[1].raw_text
	assert "Welfare of Laying Hens on Farm—2023" in references[-1].raw_text
