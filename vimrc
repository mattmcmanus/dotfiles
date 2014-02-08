set nocompatible                " choose no compatibility with legacy vi
filetype off
"
" VUNDLE
set rtp+=~/.vim/bundle/vundle/
call vundle#rc()
Bundle 'gmarik/vundle'

set t_Co=256
set noswapfile

set encoding=utf-8
set showcmd                     " display incomplete commands
"
"" Appearance!
set background=dark
colorscheme Tomorrow-Night
set number                      " line numbers
set guifont=Bitstream_Vera_Sans_Mono:h15
"
" Whitespace
set nowrap                      " don't wrap lines
set tabstop=2 shiftwidth=2      " a tab is two spaces (or set this to 4)
set expandtab                   " use spaces, not tabs (optional)
set backspace=indent,eol,start  " backspace through everything in insert mode

" Searching
set hlsearch                    " highlight matches
set incsearch                   " incremental searching
set ignorecase                  " searches are case insensitive...
set smartcase                   " ... unless they contain at least one capital letter
set wildignore+=*/tmp/*,*.so,*.swp,*.zip,*/node_modules/*     " Linux/MacOSX

" Highlight white space and tabs
set list
set listchars=tab:→\ ,trail:☢

" More bash-like tab completion
set wildmode=list:longest,full
set wildmenu

let &colorcolumn=join(range(80,999),",")

" Key Mappings
let mapleader = ","
nnoremap <leader><leader> :b#<CR>
nnoremap <c-w>- :split<CR>
nnoremap <c-w>\| :vsplit<CR>
nnoremap <c-w>/ :NERDTreeToggle<CR>
nnoremap <leader><CR> :set hlsearch!<CR>

" CtrlP Setup
"let g:ctrlp_map = '<c-p>'
"let g:ctrlp_cmd = 'CtrlP'
"let g:ctrlp_working_path_mode = ''
let g:ctrlp_map = '<leader>f'
nnoremap <silent> <leader>f :CtrlPCurWD<CR>
let g:ctrlp_custom_ignore = '\.git$\|\.hg$\|\.svn$'
let g:ctrlp_use_caching = 0
let g:ctrlp_user_command = 'ag %s -l --nocolor --hidden -g ""'
" Default to filename searches - so that appctrl will find application
" controller
let g:ctrlp_by_filename = 1


" Stripe with whitespace dummy
function! <SID>StripTrailingWhitespaces()
    " Preparation: save last search, and cursor position.
    let _s=@/
    let l = line(".")
    let c = col(".")
    " Do the business:
    silent! %s/\s\+$//e
    " Clean up: restore previous search history, and cursor position
    let @/=_s
    call cursor(l, c)
endfunction

" Remove any trailing whitespace that is in the file
autocmd BufRead,BufWrite * if ! &bin | :call <SID>StripTrailingWhitespaces() | endif


Bundle 'scrooloose/nerdtree'
"Bundle 'Lokaltog/vim-powerline'
Bundle 'mileszs/ack.vim'
"
Bundle 'tpope/vim-commentary'
Bundle 'tpope/vim-surround'
Bundle 'kien/ctrlp.vim'
Bundle 'rking/ag.vim'
Bundle 'tpope/vim-fugitive'
Bundle 'kana/vim-textobj-user'
Bundle 'nelstrom/vim-textobj-rubyblock'
Bundle 'sjl/gundo.vim'
Bundle 'abolish.vim'
Bundle 'msanders/snipmate.vim'
Bundle 'airblade/vim-gitgutter'

"" Syntax highlighting
"" --------------------------------------------------------------------------
Bundle 'tpope/vim-markdown'
Bundle 'vim-ruby/vim-ruby'
Bundle 'avakhov/vim-yaml'
Bundle 'juvenn/mustache.vim'
Bundle 'digitaltoad/vim-jade'
Bundle 'itspriddle/vim-jquery'
Bundle 'leshill/vim-json'
Bundle 'tpope/vim-rails'
Bundle 'kchmck/vim-coffee-script'
Bundle 'nono/vim-handlebars'
Bundle 'moll/vim-node'
Bundle 'pangloss/vim-javascript'
Bundle 'tpope/vim-haml'
Bundle 'wavded/vim-stylus'
Bundle 'plasticboy/vim-markdown'
Bundle 'slim-template/vim-slim'

" indent guides
"let g:indent_guides_enable_on_vim_startup = 1
"let g:indent_guides_color_change_percent = 3
"let g:indent_guides_start_level = 2
"let g:indent_guides_guide_size = 1
"Bundle 'nathanaelkane/vim-indent-guides'


set runtimepath^=~/.vim/bundle/ctrlp.vim

filetype plugin indent on       " load file type plugins + indentation
