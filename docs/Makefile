# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile gettext update-po i18n-stats html-en html-de html-fr html-es

# 从 zh_CN 源文档提取 gettext 模板（.pot）
gettext:
	@$(SPHINXBUILD) -b gettext "$(SOURCEDIR)" "$(BUILDDIR)/gettext" $(SPHINXOPTS) $(O)

# 将 .pot 合并到各语言 .po（保留已有 msgstr）
I18N_LANGS ?= en de fr es
update-po: gettext
	sphinx-intl update -p $(BUILDDIR)/gettext -l $(I18N_LANGS)

# 翻译完成度基线报告
i18n-stats:
	python3 scripts/i18n_stats.py

# 各语言 HTML 预览构建
html-en:
	@$(SPHINXBUILD) -b html -D language=en "$(SOURCEDIR)" "$(BUILDDIR)/html/en" $(SPHINXOPTS) $(O)

html-de:
	@$(SPHINXBUILD) -b html -D language=de "$(SOURCEDIR)" "$(BUILDDIR)/html/de" $(SPHINXOPTS) $(O)

html-fr:
	@$(SPHINXBUILD) -b html -D language=fr "$(SOURCEDIR)" "$(BUILDDIR)/html/fr" $(SPHINXOPTS) $(O)

html-es:
	@$(SPHINXBUILD) -b html -D language=es "$(SOURCEDIR)" "$(BUILDDIR)/html/es" $(SPHINXOPTS) $(O)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
