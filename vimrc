" Use Vim settings, rather then Vi settings. This setting must be as early as
" possible, as it has side effects.
set nocompatible

call plug#begin('~/.vim/bundle')

Plug 'tpope/vim-sensible'

" " New
Plug 'jremmen/vim-ripgrep'
Plug 'tpope/vim-eunuch'
Plug 'justinmk/vim-dirvish'
Plug 'w0rp/ale'
Plug 'tacahiroy/ctrlp-funky'
Plug 'jiangmiao/auto-pairs'

" Essentials
Plug 'ctrlpvim/ctrlp.vim'
Plug 'tpope/vim-commentary'
Plug 'tpope/vim-surround'
Plug 'godlygeek/tabular'
Plug 'tpope/vim-sleuth'
Plug 'tpope/vim-repeat'
Plug 'SirVer/ultisnips'
Plug 'honza/vim-snippets'
Plug 'tmhedberg/matchit'
Plug 'itchyny/lightline.vim'
Plug 'justincampbell/vim-eighties'
Plug 'editorconfig/editorconfig-vim'

" " Ruby
Plug 'tpope/vim-rails', { 'for' : 'ruby' }
Plug 'vim-ruby/vim-ruby', { 'for' : 'ruby' }
Plug 'tpope/vim-endwise', { 'for' : 'ruby' }
Plug 'ecomba/vim-ruby-refactoring', { 'for' : 'ruby' }
Plug 'tpope/vim-bundler', { 'for' : 'ruby' }
Plug 'jgdavey/vim-blockle', { 'for' : 'ruby' }

" Navigation/Search
Plug 'bogado/file-line'
Plug 'rking/ag.vim'
Plug 'airblade/vim-rooter'

" COLORS
Plug 'flazz/vim-colorschemes'

"GIT
Plug 'tpope/vim-fugitive'
Plug 'airblade/vim-gitgutter'

" Languages
Plug 'cakebaker/scss-syntax.vim', { 'for': 'scss' }
Plug 'tpope/vim-markdown', { 'for': ['md', 'markdown'] }
Plug 'sheerun/vim-polyglot'

" Ember
Plug 'pangloss/vim-javascript', { 'for': 'javascript' }
"Plug 'mustache/vim-mustache-handlebars'
Plug 'joukevandermaas/vim-ember-hbs'
Plug 'elzr/vim-json'
Plug 'leafgarland/typescript-vim'

call plug#end()


""
"" Basic Setup
""
set guifont=Bitstream_Vera_Sans_Mono:h15
set nocompatible      " Use vim, no vi defaults
set number            " Show line numbers
set numberwidth=3     " Always use 3 characters for line number gutter
set ruler             " Show line and column number

syntax enable         " Turn on syntax highlighting allowing local overrides
set encoding=utf-8    " Set default encoding to UTF-8
set hidden            " allow buffer switching without saving
set history=1000      " Store a ton of history (default is 20)
set cursorline        " highlight current line
set colorcolumn=80
set synmaxcol=300 " Don't try to highlight lines longer than 300 characters.

set timeout timeoutlen=1000 ttimeoutlen=100 " ensure that `O` does not cause a crazy delay

""
"" File Handling
""
set autoread
set autowrite
set nobackup
set noswapfile
set nowritebackup
set secure

""
"" Whitespace
""
set nowrap                        " don't wrap lines
set linebreak                     " don't break words
set tabstop=2 softtabstop=2 shiftwidth=2 
set expandtab                     " use spaces, not tabs
set backspace=indent,eol,start    " backspace through everything in insert mode
set autoindent                    " automatically indent to the current level

" Scrolling
set scrolloff=3                   " minimum lines to keep above and below cursor

" List chars
set list                          " Show invisible characters

set listchars=""                  " Reset the listchars
set listchars+=tab:▸\             " a tab should display as "▸ ", trailing whitespace as "."
set listchars+=trail:.            " show trailing spaces as dots
set listchars+=eol:¬              " show eol as "¬"
set listchars+=extends:>          " The character to show in the last column when wrap is
                                  " off and the line continues beyond the right of the screen
set listchars+=precedes:<         " The character to show in the last column when wrap is
                                  " off and the line continues beyond the right of the screen
""
"" Searching
""
set hlsearch    " highlight matches
set incsearch   " incremental searching
set ignorecase  " searches are case insensitive...
set smartcase   " ... unless they contain at least one capital letter

""
"" Wild settings
""
set wildmode=list:longest,list:full
set wildignore+=*.o,*.out,*.obj,.git,*.rbc,*.rbo,*.class,.svn,*.gem " Disable output and VCS files
set wildignore+=*.zip,*.tar.gz,*.tar.bz2,*.rar,*.tar.xz " Disable archive files
set wildignore+=*/vendor/gems/*,*/vendor/cache/*,*/.bundle/*,*/.sass-cache/* " Ignore bundler and sass cache
set wildignore+=*.swp,*~,._*,/tmp/ " Disable temp and backup files

""
"" Folding
""
set foldenable
set foldlevelstart=99
set foldmethod=indent

""
"" Vim UI
""
set splitbelow splitright
set guioptions=egm
set lazyredraw
set ttyfast
set title

" highlight NonText guifg=#4a4a59
" highlight SpecialKey guifg=#4a4a59

if has("mouse")
  set mouse=a
  set mousehide
  set ttymouse=xterm2
endif

"" * file type setup 		*
" automatically trim whitespace for specific file types
autocmd FileType js,c,cpp,java,php,ruby,perl autocmd BufWritePre <buffer> :%s/\s\+$//e

"""""""""""""""""""""""""
"""" *** MAPPINGS *** """
"""""""""""""""""""""""""
let mapleader = ","

" BUFFERS
nnoremap <Leader>b :ls<CR>:b<Space>
" Switch between the last two files
nnoremap <leader><leader> <c-^>

" Git
noremap <Up> :GitGutterPrevHunk<CR>
noremap <Down> :GitGutterNextHunk<CR>
" fugitive bindings
nmap <Leader>gs :Gstatus<CR>
nmap <Leader>gd :Gdiff<CR>

"" Arrow Keys Navigate QuickFix Window
noremap <Right> :cnext<CR>
noremap <Left> :cprev<CR>
noremap <Leader>j :lnext<CR>
noremap <Leader>k :lprev<CR>

nnoremap n nzz
nnoremap N Nzz
nnoremap * *zz
nnoremap # #zz
nnoremap g* g*zz
nnoremap g# g#zz

" remap jk and kj to escape in insert mode
inoremap jk <Esc>
inoremap kj <Esc>

" Normally Y copies the whole row - not from cursor to EOL like other capitals. This makes it more consistent.
noremap Y y$

" <leader>h to clear the search highlighting
nnoremap <leader>h :noh<CR>

" Toggle showing spelling errors
nnoremap <silent> <leader>s :set spell!<CR>

" Reselect visual block after indent/outdent
vnoremap < <gv
vnoremap > >gv

" Maps more bash-like keys to command line mode (colon mode)
cnoremap <C-A> <Home>
cnoremap <C-F> <Right>
cnoremap <C-B> <Left>
cnoremap <M-BS> <C-w>

"" Search for character under word
nnoremap <Leader><Leader> :Rg <cword><CR>
nnoremap <Leader>R :%s/\<<C-r><C-w>\>/
nnoremap <Leader>r :%s/<C-r><C-w>/

nnoremap \ :Rg<SPACE>

" git blame shortcut
vnoremap <Leader>g :<C-U>!git blame -w <C-R>=expand("%:p") <CR> \| sed -n <C-R>=line("'<") <CR>,<C-R>=line("'>") <CR>p <CR>

" Index ctags from any project, including those outside Rails
map <Leader>ct :!ctags -R .<CR>
nnoremap <leader>. :CtrlPTag<cr>

""""""""""""""""""""""""""""""
"""" *** AUTO COMMANDS *** """
""""""""""""""""""""""""""""""

" Remember last location in file
augroup RememberPosition
  au!
  au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$")
    \| exe "normal g'\"" | endif
augroup END

" Do not show cursorline on inactive panes
augroup CursorLine
  au!
  au VimEnter,WinEnter,BufWinEnter * setlocal cursorline
  au WinLeave * setlocal nocursorline
augroup END

"if has('autocmd')
"  " Git
"  au BufNewFile,BufRead COMMIT_EDITMSG setlocal spell!
"  au BufNewFile,BufRead COMMIT_EDITMSG call feedkeys('ggi', 't')
"endif

if has("persistent_undo")
  set undodir=~/.vim/undodir
  set undofile
endif

" CtrlP
nnoremap <leader>f :CtrlPFunky<CR>
let g:ctrlp_user_command = 'rg %s --files --color=never --glob ""'
let g:ctrlp_use_caching = 0
let g:ctrlp_funky_syntax_highlight = 1


" MISC Plugin config
let g:mustache_abbreviations = 1
let g:EditorConfig_core_mode = 'external_command'

" Tabularize 
vnoremap <Leader>= :Tabularize /=<cr>
vnoremap <Leader>: :Tabularize /:<cr>
vnoremap <Leader>, :Tabularize /,<cr>
vnoremap <Leader>" :Tabularize /"<cr>


" utilsnips
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<tab>"
let g:UltiSnipsJumpBackwardTrigger="<c-z>"
" If you want :UltiSnipsEdit to split your window.
let g:UltiSnipsEditSplit="vertical"
" Tab completion
" will insert tab at beginning of line,
" will use completion if not at beginning
function! InsertTabWrapper()
    let col = col('.') - 1
    if !col || getline('.')[col - 1] !~ '\k'
        return "\<tab>"
    else
        return "\<c-p>"
    endif
endfunction
inoremap <Tab> <c-r>=InsertTabWrapper()<cr>
inoremap <S-Tab> <c-n>

" ale
let g:ale_set_loclist = 1
let g:ale_set_quickfix = 0
let g:ale_sign_column_always = 1
let g:ale_sign_error = '💥'
let g:ale_sign_warning = '👎'
let g:ale_echo_msg_error_str = '💥'
let g:ale_echo_msg_warning_str = '🤢'
let g:ale_echo_msg_format = '[%linter%] %s [%severity%]'
highlight clear ALEErrorSign
highlight clear ALEWarningSign


set t_Co=256
set termguicolors
color Tomorrow-Night
highlight! default link Conceal Title
