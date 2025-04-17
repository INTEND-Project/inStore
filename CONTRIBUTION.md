# Contribution Guidelines

## Basic Principles to Keep in Mind
- Create a branch from any repo you would like to make contributions to and make changes in your fork. From there, you can issue pull requests back to the main branch when ready. __The common flow in the open-source community is to fork repositories to keep write access to repos as minimal as possible, this is not important for us.__ 
- Every PR must have a Github issue associated with it. The PR must reference the issue number in its commit message like so - "Fix #1"
- PRs should be kept small and manageable. No more than 1000 lines of total changes and ideally less than 500 lines.
- Rebase branches early and often to avoid merge headaches (see: merge conflict hell)

## Commits

### Structure

Title: Less than 80 characters
Include issue number as (#X) this will invoke the Github UI to link both PR and Issue
Body: Bullet points less than 100 characters in width

*I personally do not prefer the angular way of structuring commit titles (e.g., "fix(storage): failing unit test"). The aim for this is usually another tool that consumes these commit logs and generates reports and uses these prefixes accordingly. We won't be doing that so let's stick to readability (e.g., Fix failing unit test in storage module)*

#### Example
```
Add S3 implementation for the storage interface

Fix #1

* Added S3 library as a dependency
* Implemented StorageInterface methods for S3
* Implemented unit and integration tests
* ...
```

### Squashing Commits
You will probably be making several commits to the branch you are working on. To avoid cluttering the main commit log, commits in a pull request should be squashed so that there is only one commit per PR. *It is ok to make commits more higher level to encompass the whole PR*.

To squash commits, you will first need to make sure you have the latest updates
```bash
git fetch --all
```

then, rebase on the main branch
```bash
git rebase -i origin/main
```

You will be presented with something similar to this:
```
pick acdad47 Add proper file structure
pick 60aef12 Restructure Intent Manager
```

These will be your commits (from oldest to newest) that you have not pushed onto the main branch yet. To squash them into one commit, replace `pick` with `s` for all but the latest as the following:

```
s acdad47 Add proper file structure
pick 60aef12 Restructure Intent Manager
```

This will give you the opportunity to review the changes you have made as well as your commit message. Ensure to always have only one commit before opening a PR. 

You will need to force push changes to your feature branch, this is considered fine as nothing is force pushed on the main branch.

## Signing Commits
Signing commits is how we can authenticate commits, this is also a common practice in open-source contributions so it will be a good practice for us if you want to include it, but is probably not a requirement for now.
#### Generate a new GPG Key (or use an existing one if you’re comfortable with that)

o   [https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/generating-a-new-gpg-key](https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/generating-a-new-gpg-key)

#### Add the GPG Key to your Github account

o   [https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/adding-a-new-gpg-key-to-your-github-account](https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/adding-a-new-gpg-key-to-your-github-account)

#### Configure your local git tooling to use the GPG key

o   [https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/telling-git-about-your-signing-key](https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/telling-git-about-your-signing-key)

o   Be sure on this page that the right tab is open for your operating system
#### How to sign your commits

o   [https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/signing-commits](https://docs.github.com/en/github/authenticating-to-github/managing-commit-signature-verification/signing-commits)

Note that there are two “s” command line flags in the script. One is capital and one is lowercase. The capital will initiate the GPG signature and the lowercase will add “Signed by: <email_address>” as part of your commit message.

## Styling
We generally want to be following a solid styling guideline. See [PEP 8](https://peps.python.org/pep-0008/) for the official python styling guide. It is important to keep code consistent and readable, so we should try to adhere to the guide as much as possible, but prioritize keeping consitency with the repository itself.

The project is setup in a way that should give you warning and errors through linters if anything is incorrect, and formatters should be doing automatic work like keeping line lengths less than 100 characters and auto sorting imports.

### VSCode
To start development on VSCode, you will need to have Python (currently 3.10), black, pylint, and isort. To install them you may run
```bash
pip install -r dev-requirements.txt
```

Additionally, you can install their respective extensions on VSCode to enable features like in-line linting and on-save formatting. This setup will automatically use the root `pyproject.toml` configuration, so you needn't worry about setting formatting parameters yourself.

### NeoVim
For a `Packer` setup, you will need to install none-ls.nvim and configure it as follows:

```lua
local null_ls = require("null-ls")
local augroup = vim.api.nvim_create_augroup("LspFormatting", {})
null_ls.setup({
	sources = {
		null_ls.builtins.formatting.isort,
		null_ls.builtins.formatting.black.with({
			extra_args = { "--line-length=120" }
		}),
		null_ls.builtins.diagnostics.pylint,
	},
    on_attach = function(client, bufnr)
        if client.supports_method("textDocument/formatting") then
            vim.api.nvim_clear_autocmds({ group = augroup, buffer = bufnr })
            vim.api.nvim_create_autocmd("BufWritePre", {
                group = augroup,
                buffer = bufnr,
                callback = function()
                    vim.lsp.buf.format({ async = false })
                end,
            })
        end
    end,
})
```

and also configure your LSP as follows:

```lua
lspconfig = require "lspconfig"
util = require "lspconfig/util"

lspconfig.pyright.setup {
	cmd = { "pyright-langserver", "--stdio" },
	filetypes = { "python" },
	root_dir = util.root_pattern(".py"),
	settings = {
		python = {
			autoSearchPaths = true,
			diagnosticMode = "workspace",
			useLibraryCodeForTypes = true
		},
	},
}

vim.diagnostic.config({
	virtual_text = false  -- For some reason, inline erorrs and warning do not work well in python
})
vim.o.updatetime = 250
vim.cmd [[autocmd CursorHold,CursorHoldI * lua vim.diagnostic.open_float(nil, {focus=false})]]
```


