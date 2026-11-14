%% coexist.cls -- the paper class of the "Co-exist initiative of Cosmic mass universe".
%% Every paper of the initiative uses this class unchanged (PUBLISHING.md, section 2; decision D33).
%% Licence: MIT (LICENSE). Based on the standard article class.
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{coexist}[2026/11/14 v1.0 Co-exist initiative of Cosmic mass universe]

% ---------------------------------------------------------------- options
\newif\if@coexist@draft \@coexist@drafttrue
\DeclareOption{draft}{\@coexist@drafttrue}
\DeclareOption{approved}{\@coexist@draftfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[11pt,a4paper]{article}

% ---------------------------------------------------------------- packages
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{lmodern}
\RequirePackage[margin=2.5cm,headheight=14pt]{geometry}
\RequirePackage{amsmath,amssymb}
\RequirePackage{booktabs}
\RequirePackage[final]{graphicx}  % `final`: the class option `draft` must not hide figures or links
\RequirePackage[dvipsnames]{xcolor}
\RequirePackage{fancyhdr}
\RequirePackage{lastpage}
\RequirePackage{titlesec}
\RequirePackage[numbers,sort&compress]{natbib}
\RequirePackage[final,colorlinks=true,linkcolor=coexistblue,citecolor=coexistblue,urlcolor=coexistblue]{hyperref}

% ---------------------------------------------------------------- identity
\definecolor{coexistblue}{HTML}{1F4E9C}
\definecolor{coexistgrey}{HTML}{555555}
\definecolor{coexistpale}{HTML}{EEF2FA}
\newcommand{\coexistname}{Co-exist initiative of Cosmic mass universe}

% Metadata of a paper (set in the preamble)
% (\let...\@empty and \def, so that the \ifx tests for "not set" work)
\def\@paperid{PAPER-ID}\def\paperid#1{\def\@paperid{#1}}
\let\@doi\@empty\def\doi#1{\def\@doi{#1}}
\let\@keywords\@empty\def\keywords#1{\def\@keywords{#1}}
\let\@approvaldate\@empty\def\approvaldate#1{\def\@approvaldate{#1}}
\let\@engine\@empty\def\engine#1{\def\@engine{#1}}

% Declarations (fixed defaults; a paper changes them only when they are not true for it)
\newcommand{\@competing}{The authors declare no competing interests.}
\newcommand{\competinginterests}[1]{\renewcommand{\@competing}{#1}}
\newcommand{\@funding}{This work received no specific funding. It was done as open, voluntary work of the \coexistname.}
\newcommand{\funding}[1]{\renewcommand{\@funding}{#1}}
\newcommand{\@ethics}{This work uses only simulations of the virtual universe of the Cosmic Mass Lab and published
  measurements. It involves no human participants, no animals and no personal data, and needed no ethics approval.}
\newcommand{\ethics}[1]{\renewcommand{\@ethics}{#1}}
\let\@extrathanks\@empty
\def\acknowledgements#1{\def\@extrathanks{#1}}

% Authors and affiliations: \author{Name\affil{1}} and \affiliation{1}{Institution}
% Affiliation 1 is always the initiative.
\newcommand{\affil}[1]{\textsuperscript{#1}}
\newcommand{\@affiliations}{\textsuperscript{1}\coexistname}
\newcommand{\affiliation}[2]{\g@addto@macro\@affiliations{\\\textsuperscript{#1}#2}}

% ---------------------------------------------------------------- page style
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0.4pt}
\fancyhead[L]{\small\color{coexistgrey}\coexistname}
\fancyhead[R]{\small\color{coexistgrey}\if@coexist@draft Draft, not reviewed\else Preprint\fi\ \textbullet\ \@paperid}
\fancyfoot[C]{\small\color{coexistgrey}\thepage\ of \pageref{LastPage}}
\fancyfoot[L]{\if@coexist@draft\scriptsize\color{BrickRed}Not to be posted before the Board's approval\fi}
\fancyfoot[R]{\small\color{coexistgrey}\ifx\@doi\@empty\else doi:\,\@doi\fi}
\fancypagestyle{plain}{\fancyhf{}\renewcommand{\headrulewidth}{0pt}%
  \fancyfoot[C]{\small\color{coexistgrey}\thepage\ of \pageref{LastPage}}%
  \fancyfoot[L]{\if@coexist@draft\scriptsize\color{BrickRed}Not to be posted before the Board's approval\fi}%
  \fancyfoot[R]{\small\color{coexistgrey}\ifx\@doi\@empty\else doi:\,\@doi\fi}}

\titleformat{\section}{\large\bfseries\color{coexistblue}}{\thesection}{0.8em}{}
\titleformat{\subsection}{\normalsize\bfseries\color{coexistblue}}{\thesubsection}{0.6em}{}

% ---------------------------------------------------------------- title block
\renewcommand{\maketitle}{%
  % Posting before the Board's final approval breaks the rules (PUBLISHING.md, section 7; D33).
  \if@coexist@draft
    \ifx\@doi\@empty\else\ClassError{coexist}{A draft cannot carry a DOI}{Only a paper approved by the Board
      is posted on Zenodo. Remove \string\doi, or use the option `approved' after the Board's vote.}\fi
  \else
    \ifx\@approvaldate\@empty\ClassError{coexist}{The option `approved' needs \string\approvaldate}{Set the
      date of the Board's approval (PUBLISHING.md, section 3).}\fi
  \fi
  \thispagestyle{plain}%
  \begingroup\setlength{\parindent}{0pt}%
  \colorbox{coexistpale}{\parbox{\dimexpr\linewidth-2\fboxsep}{\vspace{4pt}%
    {\small\bfseries\color{coexistblue}\MakeUppercase{\coexistname}}\par\vspace{2pt}
    {\small\if@coexist@draft\color{BrickRed}DRAFT \textendash\ not yet approved by the Board; not to be posted%
      \else\color{coexistgrey}Board-reviewed preprint\fi}\vspace{4pt}}}\par\vspace{14pt}
  {\LARGE\bfseries\@title\par}\vspace{10pt}
  {\large\@author\par}\vspace{6pt}
  {\small\color{coexistgrey}\@affiliations\par}\vspace{6pt}
  {\small\color{coexistgrey}%
    \ifx\@doi\@empty\else DOI: \href{https://doi.org/\@doi}{\@doi}\quad\fi
    \ifx\@approvaldate\@empty\else Approved by the Board: \@approvaldate\quad\fi
    Licence: CC BY 4.0\par}%
  \ifx\@keywords\@empty\else\vspace{4pt}{\small\textbf{Keywords:} \@keywords\par}\fi
  \vspace{10pt}\hrule\vspace{12pt}%
  \endgroup}

\renewenvironment{abstract}{\noindent\textbf{\color{coexistblue}Abstract.}\ \small}{\par\vspace{10pt}}

% ---------------------------------------------------------------- statement labels
% Every statement is one of three kinds (CONTRIBUTING.md, rule 11); a reading L1-L8 is a hypothesis.
\newcommand{\coexisttag}[2]{\textsf{\scriptsize\colorbox{#1!15}{\textcolor{#1!70!black}{#2}}}}
\newcommand{\mathematics}{\coexisttag{OliveGreen}{MATHEMATICS}}
\newcommand{\measurement}[1]{\coexisttag{RoyalBlue}{MEASUREMENT: #1}}
\newcommand{\finding}[1]{\coexisttag{BurntOrange}{FINDING OF THE VIRTUAL UNIVERSE, LAW #1}}
\newcommand{\hypothesis}[1]{\coexisttag{Mahogany}{HYPOTHESIS #1}}

% The cosmic mass and the Composer unit
\newcommand{\G}{\mathcal{G}}
\newcommand{\cmu}{\mu}

% ---------------------------------------------------------------- mandatory sections
\newcommand{\reproducibility}{\section*{Reproducibility}\addcontentsline{toc}{section}{Reproducibility}%
  {\small Engine: \ifx\@engine\@empty\textit{(set \textbackslash engine\{release and commit\})}\else\@engine\fi.\\
   Repository: \url{https://github.com/MostafaDerraz/cosmic-mass-lab}.}\par\medskip}
\newenvironment{contributions}{\section*{Contributions and AI use}\addcontentsline{toc}{section}{Contributions and AI use}\small}%
  {\par\smallskip\noindent\textit{AI agents are credited here and are not authors
   (decision D16 of the initiative; COPE and ICMJE guidance).}\par}
\newcommand{\boardreview}[1]{\section*{Review}\addcontentsline{toc}{section}{Review}{\small
  \if@coexist@draft This paper has not yet been reviewed by the Board of the \coexistname.%
  \else Reviewed and approved by the Board of the \coexistname\ifx\@approvaldate\@empty\else\ on \@approvaldate\fi.
  Reviewers: #1.\fi}\par}

% Acknowledgements and declarations: the same fixed text in every paper of the initiative.
% A paper adds its own thanks with \acknowledgements{...} and changes a declaration only if it is not true for it.
\newcommand{\declarations}{%
  \section*{Acknowledgements}\addcontentsline{toc}{section}{Acknowledgements}%
  {\small We thank everyone who takes part in the \coexistname: the people and the AI agents who build the
   engine, run and reproduce the scenarios, ask and answer questions on the open board, review the papers and
   keep the records honest. This paper rests on that shared and open work, and on the generosity of every
   contributor who gave their time to it. We thank the members of the Board and the reviewers of this paper for
   their careful reading, and we acknowledge the theory of the cosmic mass and of General Numbers by
   Mostafa Derraz, on which the lab is built.\ifx\@extrathanks\@empty\else\ \@extrathanks\fi\par}
  \section*{Declarations}\addcontentsline{toc}{section}{Declarations}%
  {\small\setlength{\parindent}{0pt}%
   \textbf{Competing interests.} \@competing\par\smallskip
   \textbf{Funding.} \@funding\par\smallskip
   \textbf{Ethics.} \@ethics\par\smallskip
   \textbf{Data and code availability.} The engine, the scenarios, the pre-registrations and every results folder
   cited here (with its \texttt{stamp.json}) are public at
   \url{https://github.com/MostafaDerraz/cosmic-mass-lab}; code under the MIT licence, documents and results
   under CC BY 4.0.\par\smallskip
   \textbf{Use of AI.} AI agents took part in this work as described in ``Contributions and AI use''. The human
   authors checked every result and every sentence and take full responsibility for the paper.\par\smallskip
   \textbf{Publication.} \if@coexist@draft
     This is a \textbf{draft}. It has not been approved by the Board of the \coexistname\ and must not be posted,
     deposited or circulated as a publication of the initiative, on Zenodo or anywhere else, before the Board's
     final approval. Posting it earlier breaks the rules of the initiative (\texttt{PUBLISHING.md}, section 7).%
   \else
     This preprint was posted only after the final approval of the Board of the \coexistname\ on
     \@approvaldate. A version posted before that approval is not a publication of the initiative.%
   \fi\par}}

\bibliographystyle{plainnat}
\endinput
