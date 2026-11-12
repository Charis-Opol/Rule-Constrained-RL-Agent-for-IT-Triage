# Edits applied by build_manuscript.py. Executed inside that script, so it sees edit(), BS,
# ORIG_TABLES, ORIG_FIGS, table_body(), TABLES, FIGURES and counts.
#
# Placeholders the author must fill are written as \tbc{...} and print in bold brackets.

# =========================================================================== preamble

PREAMBLE = r"""%% Manuscript for Artificial Intelligence Review (Springer Nature), journal 10462.
%% Springer Nature LaTeX template (December 2024), Basic Springer Nature reference style,
%% author-year citations. Compile: pdflatex, bibtex, pdflatex, pdflatex.
%% All files sit in one folder as the journal requires (no subfolders).
\documentclass[pdflatex,sn-basic]{sn-jnl}

\usepackage{graphicx}%
\usepackage{multirow}%
\usepackage{amsmath,amssymb,amsfonts}%
\usepackage{xcolor}%
\usepackage{textcomp}%
\usepackage{manyfoot}%
\usepackage{booktabs}%
\usepackage{array}%
\usepackage{tabularx}%
\usepackage{longtable}%

\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\newcolumntype{P}[1]{>{\raggedright\arraybackslash}p{#1}}
\providecommand{\doi}[1]{\url{https://doi.org/#1}}
%% Items the author still has to supply or confirm (see open_questions.md).
\newcommand{\tbc}[1]{\textbf{[#1]}}
\setlength{\LTcapwidth}{\textwidth}

\raggedbottom

"""

# =========================================================================== front matter

ABSTRACT = (OUT / '_build' / 'abstract.txt').read_text(encoding='utf-8').strip()

FRONT = r"""\begin{document}

\title[Reinforcement learning in IT incident triage: a systematic review]{Reinforcement Learning for Investigating, Acting and Escalating in IT Incident Triage and Response: A Systematic Literature Review}

\author*{\fnm{Charis} \sur{Opol}}\email{B29654@students.ucu.ac.ug}\email{charisopol@gmail.com}

\affil*{\orgdiv{Department of Computing and Technology, Faculty of Engineering, Design and Technology}, \orgname{Uganda Christian University}, \orgaddress{\city{Kampala}, \state{Mukono District}, \country{Uganda}}}

\abstract{""" + ABSTRACT + r"""}

\keywords{Reinforcement learning, IT incident management, Incident triage, Escalation, Safe reinforcement learning, Systematic literature review}

\maketitle

\noindent ORCID: Charis Opol \url{https://orcid.org/0009-0003-7417-7984}

\begin{samepage}
\bmhead{Acknowledgements}
The author thanks Dr Innocent Ndibatya for his guidance and the colleagues who peer-reviewed this work.
\end{samepage}

"""

# =========================================================================== tables

def T(label, caption, spec, header, body, notes='', size=BS + 'footnotesize', env='table'):
    return (BS + 'begin{' + env + '}[!htbp]\n' + BS + 'caption{' + caption + '}' + BS + 'label{tab:' + label + '}\n'
            + size + '\n' + BS + 'begin{tabularx}{' + BS + 'textwidth}{' + spec + '}\n'
            + BS + 'toprule\n' + header + ' ' + BS + BS + '\n' + BS + 'midrule\n' + body + '\n'
            + BS + 'botrule\n' + BS + 'end{tabularx}\n' + notes + BS + 'end{' + env + '}')


abbrev_rows = table_body('abbrev')
for new_row in [r'IDS & Intrusion detection system \\', r'IoT & Internet of Things \\',
                r'IT & Information technology \\', r'OT & Operational technology \\',
                r'ROC-AUC & Area under the receiver operating characteristic curve \\']:
    abbrev_rows += '\n' + new_row
abbrev_rows = '\n'.join(sorted(abbrev_rows.splitlines(), key=lambda r: r.split('&')[0].strip().lower()))

TABLES['abbrev'] = T('abbrev', 'Abbreviations used in this review and their meanings',
                     '@{}lL@{}', 'Abbreviation & Meaning', abbrev_rows)

TABLES['objectives'] = T(
    'objectives',
    'Specific objectives of the review (SO1--SO5), the systematic review question (SRQ) that each answers, '
    'the research question (RQ1--RQ5) of the author\'s project that each informs, and the gap, as stated '
    'by the project\'s earlier thematic review, that motivated each objective',
    '@{}P{2.9cm}P{1.0cm}P{2.1cm}L@{}',
    'Specific objective & Review question & Project question informed & Gap that motivated it (from the thematic review)',
    table_body('objectives').replace('~' + BS + 'cite{', ' ' + BS + 'citep{'))

TABLES['keywords'] = T(
    'keywords', 'Keywords used to build the search strings and the block of the string in which each '
    'appears (A, method; B, setting; C, decision)',
    '@{}lLL@{}', 'No. & Keyword & Block', table_body('keywords'))

TABLES['strings'] = T(
    'strings', 'Search strings exactly as run on 23 October 2026 in each database, and the number of '
    'records exported from each',
    '@{}P{2.2cm}L@{}', 'Database & String as run', table_body('strings'), size=BS + 'scriptsize')

TABLES['criteria'] = T(
    'criteria', 'Eligibility criteria: the inclusion criteria (IC1--IC5) and exclusion criteria '
    '(EC1--EC7) for each aspect of a study, applied in the order shown',
    '@{}P{1.6cm}LL@{}', 'Criterion & Inclusion & Exclusion',
    table_body('criteria').replace('security incident response in IT and OT networks',
                                   'security incident response in IT and operational technology (OT) networks'))

TABLES['extraction'] = T(
    'extraction', 'Data extraction fields, grouped into bibliographic fields, fields for each specific '
    'objective (SO) and review question (SRQ), and quality ratings',
    '@{}P{2.0cm}L@{}', 'Category & Fields', table_body('extraction'))

TABLES['checklist'] = T(
    'checklist', 'Eight-item reporting and validation checklist used to appraise the included studies. '
    'For each item (Q1--Q8) the table gives the question and the condition for a rating of met, with '
    'the condition for partly met in parentheses',
    '@{}lP{2.2cm}L@{}', 'Item & Question & Rated as met when (partly met when)', table_body('checklist'))

TABLES['reconcile'] = T(
    'reconcile', 'PRISMA reconciliation: the number of records or reports ($n$) at each stage of the '
    'review and how each count is derived',
    '@{}Lrl@{}', 'Stage & $n$ & Derivation', table_body('reconcile'))

TABLES['tareasons'] = T(
    'tareasons', 'Primary reasons for excluding records at title and abstract screening, with the '
    'criterion code (Table~' + BS + 'ref{tab:criteria}) and the number of records excluded for each reason',
    '@{}lLr@{}', 'Code & Reason & Records', table_body('tareasons'))

TABLES['notret'] = T(
    'notret', 'Reports sought for retrieval but not retrieved, with the identifier used in the screening '
    'record (ID), the report title and the reason it was not retrieved',
    '@{}lLP{3.4cm}@{}', 'ID & Report & Reason', table_body('notret'))

TABLES['ftexcl'] = T(
    'ftexcl', 'Reports excluded at full-text assessment, with the identifier used in the screening '
    'record (ID), the report and the criterion and reason for its exclusion',
    '@{}lP{4.6cm}L@{}', 'ID & Report & Reason',
    table_body('ftexcl').replace(' ' + BS + 'cite{', ' ' + BS + 'citep{'))

summary_body = table_body('summary').replace('Formulation & Explicit belief',
                                             'Formulation\\textsuperscript{a} & Explicit belief', 1)
TABLES['summary'] = T(
    'summary', 'Characteristics of the 34 included studies: the number of studies by setting, '
    'publication year, formulation of the decision problem and evaluation environment',
    '@{}lLr@{}', 'Group & Category & Studies', summary_body,
    notes=BS + 'footnotetext{' + BS + 'textsuperscript{a}Formulation categories overlap; a study is counted '
    'in each that applies, and studies formulated as a fully observed MDP are not listed.}\n')

TABLES['qualsummary'] = T(
    'qualsummary', 'Quality appraisal of the 34 included studies: for each checklist item (Q1--Q8; '
    'Table~' + BS + 'ref{tab:checklist}) the number of studies rated met, partly met (Part) or not met (Not)',
    '@{}lLrrr@{}', 'Item & Question & Met & Part & Not', table_body('qualsummary'))

TABLES['coverage'] = T(
    'coverage', 'Number of included studies (of 34) that contain each element of the review questions, '
    'grouped into decisions, constraints, measures and evaluation',
    '@{}lLr@{}', 'Group & Element & Studies', table_body('coverage'))

trace_body = (table_body('trace')
              .replace('Table~' + BS + 'ref{tab:quality}', 'Table~S4 in Online Resource~1')
              .replace('repurposed IDS datasets', 'repurposed intrusion detection system (IDS) datasets'))
# Too tall for one page once author-year citations replace numbers, so set as a longtable
# (same number and caption, continued over pages).
TRACE_CAPTION = ('Thematic traceability matrix: for each review question (SRQ), the themes identified, the '
                 'studies that support each theme and the interpretation drawn. Study identifiers such as S038 are '
                 'those of the decision log (Table~S1 in Online Resource~1)')
TRACE_HEAD = 'SRQ & Theme & Supporting studies & Interpretation ' + BS + BS
TABLES['trace'] = ('{' + BS + 'scriptsize\n' + BS + 'begin{longtable}{@{}lP{2.7cm}P{4.3cm}P{3.7cm}@{}}\n'
                   + BS + 'caption{' + TRACE_CAPTION + '}' + BS + 'label{tab:trace}' + BS + BS + '\n'
                   + BS + 'toprule\n' + TRACE_HEAD + '\n' + BS + 'midrule\n' + BS + 'endfirsthead\n'
                   + BS + 'caption[]{(continued)}' + BS + BS + '\n'
                   + BS + 'toprule\n' + TRACE_HEAD + '\n' + BS + 'midrule\n' + BS + 'endhead\n'
                   + BS + 'botrule\n' + BS + 'endfoot\n'
                   + trace_body + '\n' + BS + 'end{longtable}\n}')

# =========================================================================== figures

def F(label, file, caption):
    return (BS + 'begin{figure}[!htbp]\n' + BS + 'centering\n' + BS + 'includegraphics{' + file + '}\n'
            + BS + 'caption{' + caption + '}' + BS + 'label{fig:' + label + '}\n' + BS + 'end{figure}')


FIGURES['prisma'] = F(
    'prisma', 'Fig1',
    'PRISMA 2020 flow diagram for this review, which searched databases only; citation searching was '
    'not carried out. The left-hand boxes give the number of records or reports at each stage, from '
    'identification through screening to inclusion, and the right-hand boxes give the number removed or '
    'excluded at that stage, with the reasons')

FIGURES['coverage'] = F(
    'coverage', 'Fig2',
    'Horizontal bar chart of the number of included studies, out of 34, that contain each element of the '
    'review questions. From top to bottom the bars show the decisions made (gathers information, response '
    'action, escalates or defers, all three decisions), constraint handling (hard filter or shield, blocked '
    'action handled), the measures reported (decision quality, efficiency, escalation, compliance) and '
    'robustness testing. Each bar is labelled with its count')

FIGURES['evidence'] = F(
    'evidence', 'Fig3',
    'Components of the planned agent (left column) and the included evidence for each (right column). '
    'Explicit belief over the hidden incident cause: 4 studies, all in security '
    + BS + 'cite{hammar2026belief,hammar2025,kovtun2026,koupaei2026}. Costed investigate action: 17 studies, '
    'with effort reduced in ' + BS + 'cite{wu2026,kovtun2026}. Learned escalation: 7 studies, learned in four, '
    'all in security ' + BS + 'cite{bhosale2026,alturkistani2022,sahin2026,kovtun2026}. Rule mechanism with '
    'blocked-action handling: 5 studies with hard filters, of which 3 report how a blocked action is handled '
    'and none allows a re-proposal. The hatched box at the bottom states that no study combines all four '
    'components for IT service incidents')

# =========================================================================== introduction

edit('introduction', BS + 'section{Introduction}', BS + 'section{Introduction}' + BS + 'label{sec:intro}',
     'Label for cross-references from the declarations')
edit('introduction', BS + 'IEEEPARstart{O}{rganisations} depend on IT services',
     'Organisations depend on information technology (IT) services',
     'IEEEtran drop cap removed; IT defined at first mention (guideline: abbreviations)')
edit('introduction',
     'In both descriptions, triage is a set of decisions made before the cause of the incident is known.',
     'In both descriptions, triage is a set of decisions made before the cause of the incident is known. '
     'The abbreviations used in this review are listed in Table~' + BS + 'ref{tab:abbrev}.\n\n%%TABLE:abbrev%%\n',
     'Table 1 was never cited in the text; citation added so tables are cited in order (guideline: tables)')
edit('introduction', 'is listed in Appendix~' + BS + 'ref{app:decisionlog}',
     'is listed in Table~S1 of Online Resource~1',
     'Appendix A moved to Supplementary Information, cited as Online Resource (guideline: SI numbering)')
edit('introduction', 'The review addresses five questions:',
     'The review addresses five systematic review questions (SRQ1--SRQ5):',
     'SRQ defined at first mention (guideline: abbreviations)')
edit('introduction', 'formulated as MDP, POMDP or RL problems',
     'formulated as Markov decision process (MDP), POMDP or RL problems',
     'MDP defined at first mention (guideline: abbreviations)')

# =========================================================================== methods

edit('methodology', BS + 'section{Methodology (PRISMA Protocol)}', BS + 'section{Methods}',
     'Heading aligned with the guideline wording, which requires LLM use to be documented in the Methods section')
edit('methodology', 'reported according to the PRISMA 2020 guideline',
     'reported according to the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 guideline',
     'PRISMA defined at first mention (guideline: abbreviations)')
edit('methodology', 'where much AIOps work appears',
     'where much work on artificial intelligence for IT operations (AIOps) appears',
     'AIOps defined at first mention (guideline: abbreviations)')
edit('methodology', 'as data items in the extraction form (Table~' + BS + 'ref{tab:extraction}).',
     'as data items in the extraction form (Section~' + BS + 'ref{sec:extraction}).',
     'Table 6 was cited before Table 5; pointer changed to the section so tables are cited in order (guideline: tables)')
edit('methodology', 'The criteria in Table~' + BS + 'ref{tab:criteria} were written before screening',
     'The inclusion criteria (IC1--IC5) and exclusion criteria (EC1--EC7) in Table~' + BS + 'ref{tab:criteria} were written before screening',
     'IC and EC defined at first mention (guideline: abbreviations)')
edit('methodology',
     'The title and abstract decisions and the full-text assessments of the reports on file were made with an AI assistant, '
     'and two full-text decisions were made manually (Section~' + BS + 'ref{sec:results}).',
     'The title and abstract decisions and the full-text assessments of the reports on file were made with the AI assistant '
     'described in Section~' + BS + 'ref{sec:ai}, and two full-text decisions were made manually (Section~' + BS + 'ref{sec:results}).',
     'Points to the single account of AI use in the Methods (guideline: LLM use documented in Methods)')
edit('methodology', 'are listed in Appendix~' + BS + 'ref{app:decisionlog}.',
     'are listed in Table~S1 of Online Resource~1.',
     'Appendix A moved to Supplementary Information (guideline: SI numbering)')
edit('methodology', BS + 'subsection{Data Extraction}',
     BS + 'subsection{Data Extraction}' + BS + 'label{sec:extraction}',
     'Label for the section cross-reference that replaces the out-of-order table citation')
edit('methodology', 'The ratings were made with the AI assistance declared at the end of this paper and have not been independently checked.',
     'The ratings were made with the AI assistant described in Section~' + BS + 'ref{sec:ai} and have not been independently checked.',
     'Points to the single account of AI use in the Methods (guideline: LLM use documented in Methods)')
edit('methodology', 'the full mapping is given in Table~' + BS + 'ref{tab:trace} and in the traceability files that accompany this review.',
     'the full mapping is given in Section~' + BS + 'ref{sec:trace} and in the traceability files in Online Resource~2.',
     'Table 15 was cited before Tables 8 to 14; pointer changed to the section (guideline: tables); audit files cited as Online Resource 2')
edit('methodology', 'The review is accompanied by a set of audit files:',
     'The review is accompanied by a set of audit files (Online Resource~2; see also the data availability statement):',
     'Audit files cited as Supplementary Information and linked to the Data Availability statement')
edit('methodology', 'The tables and counts in this paper are generated from these files.',
     'The tables and counts in this paper are generated from these files.\n\n'
     + BS + 'subsection{Use of an AI Assistant}' + BS + 'label{sec:ai}\n\n'
     'An AI assistant, Claude Opus 5.5 (Anthropic), was used in conducting this review. '
     'It supported the development of the search strings, the eligibility criteria and the data-processing scripts. '
     'The title and abstract decisions for all 131 screened records, the full-text assessments of the reports on file '
     'other than the two decided manually, the data extraction and the quality ratings were made with the assistant. '
     'The database searches, the retrieval of the full texts, the direction and framing of the review, and the full-text '
     'decisions for two reports were completed independently of the assistant. None of the decisions made with the '
     'assistant was independently duplicated, and no measure of agreement was computed; this limitation is discussed in '
     'Section~' + BS + 'ref{sec:limitations}. The author is accountable for every decision reported in this review and '
     'for the content of this article.',
     'Single factual account of LLM use in the Methods, replacing the end-of-paper declaration; limitation kept '
     '(guideline: LLM use documented in Methods; human accountability)')

# =========================================================================== results

edit('results', 'Figure~' + BS + 'ref{fig:prisma} shows the flow', 'Fig.~' + BS + 'ref{fig:prisma} shows the flow',
     'Springer figure citation style')
edit('results', '%%TABLE:tareasons%%\n\n%%TABLE:reconcile%%', '%%TABLE:reconcile%%\n\n%%TABLE:tareasons%%',
     'Reconciliation table is cited before the reasons table, so it now comes first (guideline: tables cited in order)')
edit('results', BS + 'input{figures/prisma_flow}', '%%FIGURE:prisma%%', 'Fig. 1 now an EPS file (guideline: artwork)')
edit('results', BS + 'input{figures/fig_coverage}', '%%FIGURE:coverage%%', 'Fig. 2 now an EPS file (guideline: artwork)')
edit('results', 'Appendix~' + BS + 'ref{app:decisionlog} gives the outcome for every report sought.',
     'Table~S1 of Online Resource~1 gives the outcome for every report sought.',
     'Appendix A moved to Supplementary Information')
edit('results', 'and Appendix~' + BS + 'ref{app:characteristics} describes each one.',
     'and Table~S2 of Online Resource~1 describes each one.', 'Appendix B moved to Supplementary Information')
edit('results', 'alert triage in security operations centres,', 'alert triage in security operations centres (SOCs),',
     'SOC defined at first mention (guideline: abbreviations)')
edit('results', 'industrial and IoT systems', 'industrial and Internet of Things (IoT) systems',
     'IoT defined at first mention (guideline: abbreviations)')
edit('results', 'chiefly the CAGE-2 and CAGE-4 cyber-defence gyms',
     'chiefly the CAGE-2 and CAGE-4 cyber-defence gyms (Cyber Autonomy Gym for Experimentation)',
     'CAGE defined at first mention (guideline: abbreviations)')
edit('results', 'Appendix~' + BS + 'ref{app:quality} gives every rating.', 'Table~S4 of Online Resource~1 gives every rating.',
     'Appendix D moved to Supplementary Information')
edit('results', 'Appendix~' + BS + 'ref{app:coverage} records the elements study by study.',
     'Table~S3 of Online Resource~1 records the elements study by study.', 'Appendix C moved to Supplementary Information')
edit('results', 'against 6.1 for a plain DQN', 'against 6.1 for a plain deep Q-network (DQN)',
     'DQN defined at first mention (guideline: abbreviations)')
edit('results', 'from $O(N^2)$ to $O(1)$', 'from $' + BS + 'mathrm{O}(N^{2})$ to $' + BS + 'mathrm{O}(1)$',
     'Upright operator, italic variable (guideline: scientific style)')
edit('results', '(142~s to 144~s)', '(142' + BS + ',s to 144' + BS + ',s)', 'SI unit spacing (guideline: SI units)')
edit('results', 'than an unshielded PPO agent', 'than an unshielded proximal policy optimisation (PPO) agent',
     'PPO defined at first mention (guideline: abbreviations)')
edit('results', 'through accuracy, reward, cost, recall or MCC,', 'through accuracy, reward, cost, recall or the Matthews correlation coefficient (MCC),',
     'MCC defined at first mention (guideline: abbreviations)')
edit('results', 'whose failure F1 and ROC-AUC concealed and MCC revealed',
     'whose failure the F1 score and the area under the receiver operating characteristic curve (ROC-AUC) concealed and MCC revealed',
     'ROC-AUC defined at first mention (guideline: abbreviations)')
edit('results', 'rose from 41.2~s to 79.4~s at peak load', 'rose from 41.2' + BS + ',s to 79.4' + BS + ',s at peak load',
     'SI unit spacing (guideline: SI units)')
edit('results', 'in about 15 to 19 seconds, against more than 30 minutes for PPO',
     'in about 15' + BS + ',s to 19' + BS + ',s, against more than 30' + BS + ',min for PPO',
     'SI unit symbols (guideline: SI units)')
edit('results', BS + 'subsection{Thematic Traceability}', BS + 'subsection{Thematic Traceability}' + BS + 'label{sec:trace}',
     'Label for the section cross-reference from the Methods')

# =========================================================================== discussion

edit('discussion', 'as Turan et al.' + BS + ' argue it should be~' + BS + 'cite{turan2026}',
     'as Turan argues it should be~' + BS + 'cite{turan2026}',
     'Citation error: arXiv:2606.08919 has a single author (E. Turan), so "et al." was wrong')

edit('limitations', 'Section~' + BS + 'ref{sec:screening} and Appendix~' + BS + 'ref{app:decisionlog} state',
     'Section~' + BS + 'ref{sec:screening} and Table~S1 of Online Resource~1 state',
     'Appendix A moved to Supplementary Information')

# =========================================================================== post-processing

def POSTPROCESS(s):
    s = s.replace('Sahin and Mert', BS + 'c{S}ahin and Mert')
    s = s.replace('–', '--').replace('—', '---').replace('’', "'").replace(' ', ' ')
    return s

# =========================================================================== back matter

BACK = r"""

\backmatter

\bmhead{Supplementary information}
The online version contains supplementary material.
\textbf{Online Resource 1} (ESM\_1.pdf): Tables S1--S4, which give the outcome of every report sought for retrieval (S1), the task, formulation, environment and main result of each included study (S2), the coding of the review-question elements for each included study (S3), and the quality rating of each included study on items Q1--Q8 (S4).
\textbf{Online Resource 2} (ESM\_2.xlsx): the audit files of the review, one worksheet each: the decision and reason for each of the 131 screened records, the outcome for each of the 47 reports sought, the data extraction form and the quality ratings of the 34 included studies, the study and thematic traceability matrices, and the reconciliation of every PRISMA count.

\section*{Statements and Declarations}

\bmhead{Funding}
No funding was received for conducting this study.

\bmhead{Competing interests}
The author has no relevant financial or non-financial interests to disclose.

\bmhead{Ethics approval and consent to participate}
Not applicable. This review synthesises published studies; it involved no human participants, personal data or animals.

\bmhead{Consent for publication}
Not applicable.

\bmhead{Data availability}
The audit files that support the findings of this review are provided as Online Resource~2: the decision and reason for every screened record (\texttt{exclusion\_traceability.csv}), the outcome of every report sought (\texttt{fulltext\_decisions.csv}), the extraction form (\texttt{data\_extraction.csv}), the quality ratings (\texttt{quality\_appraisal.csv}), the study and thematic traceability matrices, the reconciliation of every PRISMA count (\texttt{prisma\_reconciliation.csv}), and the screening and table-generation scripts. The raw database exports and the full texts of the included studies are not shared, because the database licence terms and the publishers' copyright restrict their redistribution; the exports can be recreated by running the search strings in Table~\ref{tab:strings}.

\bmhead{Materials and code availability}
The scripts that combined the exports, applied the automated filters and generated the tables and counts are included in Online Resource~2 (see Data availability). No other materials were produced.

\bmhead{Author contributions}
Charis Opol is the sole author. She conceived and designed the review, ran the database searches, retrieved the full texts, conducted the screening, data extraction and quality appraisal with the AI assistance described in Section~\ref{sec:ai}, synthesised the evidence, and wrote and revised the manuscript. She read and approved the final manuscript.

\bmhead{Use of artificial intelligence tools}
The use of an AI assistant in conducting this review is described in Section~\ref{sec:ai}.

\bmhead{Prior dissemination and re-use of material}
This review was prepared during the author's undergraduate research project at Uganda Christian University. Parts of the Introduction (the description of incident management and triage, the framing of triage as a sequence of decisions, and the requirements for rule enforcement and escalation) and the gap statements in Table~\ref{tab:objectives} draw on, and in places repeat wording from, Chapters One and Two of the author's project report, \emph{Investigate, Recommend or Escalate: A Rule-Constrained Reinforcement Learning Agent for IT Incident Triage under Ambiguous Evidence} (Uganda Christian University, 2026), which also summarises some findings of this review. The report is an unpublished university assessment document and has not been published or submitted to any journal.

\bibliography{references}

\end{document}
"""
