" Use Vim settings, rather then Vi settings. This setting must be as early as
" possible, as it has side effects.
set nocompatible

call plug#begin('~/.vim/bundle')

Plug 'sensible.vim'

" Languages
"   Ruby
Plug 'vim-ruby/vim-ruby', { 'for': 'ruby' }
Plug 'tpope/vim-rails', { 'for': 'ruby' }
Plug 'ecomba/vim-ruby-refactoring', { 'for': 'ruby' }
Plug 'nelstrom/vim-textobj-rubyblock', { 'for': 'ruby' }
Plug 'tpope/vim-endwise', { 'for': 'ruby' }
"   JavaScript
Plug 'jelera/vim-javascript-syntax', { 'for': 'javascript' }
Plug 'kchmck/vim-coffee-script', { 'for': 'coffee' }
Plug 'leshill/vim-json', { 'for': ['javascript','json'] }
Plug 'itspriddle/vim-jquery', { 'for': ['javascript', 'coffee'] }
Plug 'jshint.vim', { 'for': 'javascript' }
Plug 'mxw/vim-jsx', { 'for': 'jsx' }
Plug 'mtscout6/vim-cjsx', { 'for': 'cjsx' }
"   HTML
Plug 'xenoterracide/html.vim'
Plug 'tudorprodan/html_annoyance.vim'
"   Other
Plug 'slim-template/vim-slim', { 'for': 'slim' }
Plug 'tpope/vim-markdown'
Plug 'avakhov/vim-yaml'
Plug 'juvenn/mustache.vim'
Plug 'mustache/vim-mustache-handlebars'
Plug 'digitaltoad/vim-jade', { 'for': 'jade' }
Plug 'cakebaker/scss-syntax.vim', { 'for': 'scss' }
Plug 'hail2u/vim-css3-syntax'

Plug 'tpope/vim-vinegar'
Plug 'kien/ctrlp.vim'
Plug 'tpope/vim-fugitive'
Plug 'sjl/gundo.vim', { 'on': 'GundoToggle' }
Plug 'rking/ag.vim', { 'on': 'Ag' }
Plug 'tpope/vim-commentary'
Plug 'airblade/vim-gitgutter'
Plug 'nathanaelkane/vim-indent-guides'
Plug 'chriskempson/base16-vim'

Plug 'danro/rename.vim', { 'on': 'Rename' }
Plug 'tpope/vim-surround'
Plug 'vim-scripts/argtextobj.vim'
Plug 'Townk/vim-autoclose'
Plug 'scrooloose/syntastic'
Plug 'godlygeek/tabular'
Plug 'Align'
Plug 'michaeljsmith/vim-indent-object'
Plug 'tpope/vim-repeat'
Plug 'matchit.zip'
Plug 'abolish.vim'
Plug 'bogado/file-line'
Plug 'dockyard/vim-easydir'
Plug 'jgdavey/vim-blockle'
Plug 'kien/rainbow_parentheses.vim'
Plug 'justincampbell/vim-eighties'

" SnipMate and dependencies
Plug 'MarcWeber/vim-addon-mw-utils'
Plug 'tomtom/tlib_vim'
Plug 'honza/vim-snippets'
Plug 'garbas/vim-snipmate'

Plug 'editorconfig/editorconfig-vim'

call plug#end()



set guioptions=egm
set guifont=Bitstream_Vera_Sans_Mono:h15
set antialias
set t_Co=256
set t_ut=
set background=dark
let base16colorspace=256
colorscheme base16-default

" Index ctags from any project, including those outside Rails
map <Leader>ct :!ctags -R .<CR>

" Switch between the last two files
nnoremap <leader><leader> <c-^>

" Get off my lawn
noremap <Up> :cnext<CR>
noremap <Down> :cprev<CR>
noremap <Leader><Up> :GitGutterLineHighlightsToggle<CR>
noremap <Leader><Left> :GitGutterPrevHunk<CR>
noremap <Leader><Right> :GitGutterNextHunk<CR>

" Snippets are activated by Shift+Tab
let g:snippetsEmu_key = "<S-Tab>"

let g:ctrlp_use_caching = 0

" Treat <li> and <p> tags like the block tags they are
let g:html_indent_tags = 'li\|p'

" Open new split panes to right and bottom, which feels more natural
set splitbelow
set splitright

set omnifunc=csscomplete#CompleteCSS

" JSNavigate; javascript_spec_navigator.vim
noremap <leader>z :call JsSpecNavigate()<CR>

let g:netrw_liststyle=0
set noswapfile


nnoremap n nzz
nnoremap N Nzz
nnoremap * *zz
nnoremap # #zz
nnoremap g* g*zz
nnoremap g# g#zz





" Put temp files in common directory
set backupdir=~/.vim/backup
set directory=~/.vim/backup

" prevent the directory-specific vimrc files from executing potentially dangerous commands
set secure

" More bash-like tab completion
set wildmode=longest,list,full
set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/tmp/cache/*,*/*.jpg,*/*.png,*/*.pyc

set smartindent

" Fold by syntax, start full open
set foldenable
set foldlevelstart=99

set autoread

""""""""""""
""" Tabs """
""""""""""""

" Use 2-space tabs
set softtabstop=2
set shiftwidth=2
set tabstop=2
set expandtab

""""""""""""""""
""" Spelling """
""""""""""""""""

" Use english for spellchecking
set spl=en spell
set nospell


""""""""""""""
""" Search """
""""""""""""""

" highlight search results
set hlsearch

" Ignore case on search unless search has uppercase characters
set ignorecase
set smartcase


"""""""""""""""
""" Visuals """
"""""""""""""""

" Use relative line numbers, but show the absolute number on the current line
"set relativenumber
set number

" Show whitespace as unicode chars
set listchars=tab:‣\ ,trail:\ ,extends:…,precedes:…,nbsp:˖
set list

set colorcolumn=80

" speed up macros and repeated commands
set lazyredraw

if has("mouse")
  set mouse=a
  set mousehide
  set ttymouse=xterm2
endif

""""""""""""""""""""""""
""" *** MAPPINGS *** """
""""""""""""""""""""""""

" remap jk and kj to escape in insert mode
inoremap jk <Esc>
inoremap kj <Esc>

" Normally Y copies the whole row - not from cursor to EOL like other capitals. This makes it more consistent.
noremap Y y$

" Make K split lines (the opposite of J)
nnoremap K i<cr><esc>k$

" Make <leader>k split the line after the cursor
nnoremap <leader>k a<cr><esc>k$

" Insert new line above cursor
nnoremap <C-K> O<Esc>j

" Insert new line below cursor
nnoremap <C-J> o<Esc>k

" Insert space after cursor
nnoremap <C-L> li <Esc>h

" Insert space before cursor
nnoremap <C-H> i <Esc>l

" 'Q' runs the macro in the 'q' register, instead of opening ex mode.
nnoremap Q @q

" Fast saving
nnoremap <leader>w :w!<cr>

" Return cursor to start of edit after repeat
nnoremap . .`[

" Hit TAB twice to switch to the next window
nnoremap <tab><tab> <C-w>w
nnoremap <s-tab><s-tab> <C-w>W

" <leader>h to clear the search highlighting
nnoremap <leader>h :noh<CR>

" Toggle showing spelling errors
nnoremap <silent> <leader>s :set spell!<CR>

" use . to repeat a change for every line in the block
vnoremap <silent> . :normal .<CR>

" Reselect visual block after indent/outdent
vnoremap < <gv
vnoremap > >gv

" :W also saves
cnoreabbrev W w

" Force Saving Files that Require Root Permission
cnoremap w!! %!sudo tee > /dev/null %

" Maps more bash-like keys to command line mode (colon mode)
cnoremap <C-A> <Home>
cnoremap <C-F> <Right>
cnoremap <C-B> <Left>
cnoremap <M-BS> <C-w>


"""""""""""""""""""""""""""""
""" *** AUTO COMMANDS *** """
"""""""""""""""""""""""""""""

if has('autocmd')
  " Git
  au BufNewFile,BufRead COMMIT_EDITMSG setlocal spell!
  au BufNewFile,BufRead COMMIT_EDITMSG call feedkeys('ggi', 't')
endif

augroup VimCSS3yntax
  autocmd!

  autocmd FileType css setlocal iskeyword+=-
  autocmd FileType scss setlocal iskeyword+=-
  au BufNewFile,BufRead *.scss set ft=scss.css
augroup END

""""""""""""""
""" CTRL P """
""""""""""""""

let g:ctrlp_custom_ignore = '\.git$\|tmp$\|\.bundle$\|public/uploads$\|public/system$\|public\/topics$\|public/user_profiles\|\.sass-cache$|node_modules$'


" Use The SilverSearcher to find files. It means we no longer need to cache.
let g:ag_binary = system("which ag | xargs echo -n")
if filereadable(g:ag_binary)
  let g:ctrlp_user_command = g:ag_binary . ' %s -l --nocolor -g ""'
endif

let g:ctrlp_use_caching = 0

"""""""""""""""""""""""""""""""""""""""
""" Visual Mode */# from Scrooloose """
"""""""""""""""""""""""""""""""""""""""

function! s:VSetSearch()
  let temp = @@
  norm! gvy
  let @/ = '\V' . substitute(escape(@@, '\'), '\n', '\\n', 'g')
  let @@ = temp
endfunction

vnoremap * :<C-u>call <SID>VSetSearch()<CR>//<CR><c-o>
vnoremap # :<C-u>call <SID>VSetSearch()<CR>??<CR><c-o>


""""""""""""""""""""""
""" Rainbow Parens """
""""""""""""""""""""""

au VimEnter * RainbowParenthesesToggle
au Syntax * RainbowParenthesesLoadRound
au Syntax * RainbowParenthesesLoadSquare
au Syntax * RainbowParenthesesLoadBraces


""""""""""""""""""
""" Tabularize """
""""""""""""""""""

if exists(":Tabularize")
  " align =
  nnoremap <Leader>a= :Tabularize /^[^=]*\zs=/l1<CR>
  vnoremap <Leader>a= :Tabularize /^[^=]*\zs=/l1<CR>

  " align : but without a space before them
  nnoremap <Leader>a: :Tabularize/\(:.*\)\@<!:\zs /l0<CR>
  vnoremap <Leader>a: :Tabularize/\(:.*\)\@<!:\zs /l0<CR>

  " align {
  nnoremap <Leader>a{ :Tabularize /^[^{]*\zs{/l1<CR>
  vnoremap <Leader>a{ :Tabularize /^[^{]*\zs{/l1<CR>

  " align ,'s, but without a space before them
  nnoremap <Leader>a, :Tabularize /,\zs/l0r1<CR>
  vnoremap <Leader>a, :Tabularize /,\zs/l0r1<CR>
endif

let g:indent_guides_auto_colors = 0
let g:indent_guides_enable_on_vim_startup = 1
let g:indent_guides_color_change_percent  = 3
let g:indent_guides_start_level           = 2
let g:indent_guides_guide_size            = 1

let g:EditorConfig_core_mode = 'external_command'

let g:syntastic_javascript_checkers = ['jshint']
let g:syntastic_html_tidy_ignore_errors = [
    \  'plain text isn''t allowed in <head> elements',
    \  '<base> escaping malformed URI reference',
    \  'discarding unexpected <body>',
    \  '<script> escaping malformed URI reference',
    \  '</head> isn''t allowed in <body> elements'
    \ ]
