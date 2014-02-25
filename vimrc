set nocompatible                " choose no compatibility with legacy vi
filetype off
set t_Co=256
set nobackup
set nowritebackup
set noswapfile    " http://robots.thoughtbot.com/post/18739402579/global-gitignore#comment-458413287
set encoding=utf-8
set showcmd                     " display incomplete commands
set nowrap                      " don't wrap lines
set tabstop=2 shiftwidth=2      " a tab is two spaces (or set this to 4)
set expandtab                   " use spaces, not tabs (optional)
set backspace=indent,eol,start  " backspace through everything in insert mode
set history=50
set ruler         " show the cursor position all the time
set incsearch     " do incremental searching
set laststatus=2  " Always display the status line
set autowrite     " Automatically :write before running commands

"

" Searching
set hlsearch                    " highlight matches
set incsearch                   " incremental searching
set ignorecase                  " searches are case insensitive...
set smartcase                   " ... unless they contain at least one capital letter
set wildignore+=*/tmp/*,*.so,*.swp,*.zip,*/node_modules/*     " Linux/MacOSX

" Highlight white space and tabs
set list
set list listchars=tab:»·,trail:·

if filereadable(expand("~/.vimrc.bundles"))
  source ~/.vimrc.bundles
endif

"" Appearance!
set background=dark
colorscheme Tomorrow-Night
set number                      " line numbers
set guifont=Bitstream_Vera_Sans_Mono:h15

let &colorcolumn=join(range(80,999),",")

" Key Mappings
let mapleader = ","
nnoremap <c-w>- :split<CR>
nnoremap <c-w>\| :vsplit<CR>
nnoremap <c-w>/ :NERDTreeToggle<CR>
nnoremap <leader>n :NERDTreeFind<CR>
nnoremap <leader><CR> :set hlsearch!<CR>
" don't unselect after move
vmap < <gv
vmap > >gv
vmap <TAB> >gv
vmap <S-TAB> <gv

" Index ctags from any project, including those outside Rails
map <Leader>ct :!ctags -R .<CR>

" Switch between the last two files
nnoremap <leader><leader> <c-^>

" Get off my lawn
nnoremap <Left> :echoe "Use h"<CR>
nnoremap <Right> :echoe "Use l"<CR>
nnoremap <Up> :echoe "Use k"<CR>
nnoremap <Down> :echoe "Use j"<CR>

" Snippets are activated by Shift+Tab
let g:snippetsEmu_key = "<S-Tab>"

" Tab completion
" will insert tab at beginning of line,
" will use completion if not at beginning
set wildmenu
set wildmode=list:longest,list:full
set complete=.,w,t
function! InsertTabWrapper()
    let col = col('.') - 1
    if !col || getline('.')[col - 1] !~ '\k'
        return "\<tab>"
    else
        return "\<c-p>"
    endif
endfunction
inoremap <Tab> <c-r>=InsertTabWrapper()<cr>

" CtrlP Setup
let g:ctrlp_map = '<leader>f'
nnoremap <silent> <leader>f :CtrlPCurWD<CR>
let g:ctrlp_custom_ignore = '\.git$\|\.hg$\|\.svn$'

" Use The Silver Searcher https://github.com/ggreer/the_silver_searcher
if executable('ag')
  " Use Ag over Grep
  set grepprg=ag\ --nogroup\ --nocolor

  " Use ag in CtrlP for listing files. Lightning fast and respects .gitignore
  let g:ctrlp_user_command = 'ag %s -l --nocolor --hidden -g ""'

  " ag is fast enough that CtrlP doesn't need to cache
  let g:ctrlp_use_caching = 0
endif

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

" indent guides
let g:indent_guides_enable_on_vim_startup = 1
let g:indent_guides_color_change_percent = 3
let g:indent_guides_start_level = 2
let g:indent_guides_guide_size = 1

set runtimepath^=~/.vim/bundle/ctrlp.vim

filetype plugin indent on       " load file type plugins + indentation

" Treat <li> and <p> tags like the block tags they are
let g:html_indent_tags = 'li\|p'

" Open new split panes to right and bottom, which feels more natural
set splitbelow
set splitright

" Quicker window movement
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-h> <C-w>h
nnoremap <C-l> <C-w>l

" configure syntastic syntax checking to check on open as well as save
let g:syntastic_check_on_open=1

" JSNavigate; javascript_spec_navigator.vim
noremap <leader>z :call JsSpecNavigate()<CR>

augroup WhiteSpaceKilla
  au!
  " Remove any trailing whitespace that is in the file
  autocmd BufRead,BufWrite * if ! &bin | :call <SID>StripTrailingWhitespaces() | endif
augroup end

augroup NewSyntaxes
  au!
  " rabl is ruby
  au BufRead,BufNewFile *.rabl setf ruby
  au BufRead,BufNewFile *.hamlc set ft=haml
  au BufRead,BufNewFile *.skim set ft=slim
augroup end
