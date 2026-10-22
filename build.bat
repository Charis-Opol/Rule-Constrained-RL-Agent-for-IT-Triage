@echo off
rem Builds the thesis and the milestone and stakeholder documents with Tectonic.
rem tools\tectonic.exe is not in the repository: download Tectonic from https://tectonic-typesetting.github.io
rem and place tectonic.exe in tools\. The first run downloads LaTeX packages and needs an internet connection.
cd /d "%~dp0"
set TT=%~dp0tools\tectonic.exe

pushd research\thesis
"%TT%" main.tex
popd

pushd research\slr
"%TT%" slr_review.tex
popd

pushd documentation\milestone
"%TT%" midsemester_summary.tex
"%TT%" talking_points.tex
popd

pushd documentation\stakeholder\proposal
"%TT%" proposal_mr_simon.tex
popd

pushd documentation\stakeholder\letter
"%TT%" letter_to_director.tex
popd

pause
