" Use Vim settings, rather then Vi settings. This setting must be as early as
" possible, as it has side effects.
set nocompatible

call plug#begin('~/.vim/bundle')

Plug 'tpope/vim-sensible'

" New
Plug 'jremmen/vim-ripgrep'
Plug 'gko/vim-coloresque'
Plug 'benizi/vim-automkdir'
Plug 'leafgarland/typescript-vim'
Plug 'w0rp/ale'

" Essentials
Plug 'ctrlpvim/ctrlp.vim'
Plug 'tpope/vim-vinegar'
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

" Ruby
Plug 'tpope/vim-rails', { 'for' : 'ruby' }
Plug 'vim-ruby/vim-ruby', { 'for' : 'ruby' }
Plug 'tpope/vim-endwise', { 'for' : 'ruby' }
Plug 'ecomba/vim-ruby-refactoring', { 'for' : 'ruby' }
Plug 'tpope/vim-bundler', { 'for' : 'ruby' }
Plug 'jgdavey/vim-blockle'

" Navigation/Search
Plug 'bogado/file-line'
Plug 'rking/ag.vim'
Plug 'airblade/vim-rooter'

" COLORS
Plug 'chriskempson/base16-vim'
Plug 'joshdick/onedark.vim'
Plug 'kien/rainbow_parentheses.vim'

"GIT
Plug 'tpope/vim-fugitive'
Plug 'airblade/vim-gitgutter'

" Languages
Plug 'cakebaker/scss-syntax.vim', { 'for': 'scss' }
Plug 'tpope/vim-markdown', { 'for': ['md', 'markdown'] }

" Ember
Plug 'pangloss/vim-javascript', { 'for': 'javascript' }
Plug 'sheerun/vim-polyglot'
Plug 'joukevandermaas/vim-ember-hbs'
Plug 'AndrewRadev/ember_tools.vim'

call plug#end()

" ------------
" better defaults
" -----------
set nobackup
set nowritebackup
set noswapfile
set secure
set autoread
set t_Co=256

"set autoindent
scriptencoding utf-8
set number
set autoread
set wildmode=list:longest,list:full
set wildignore+=*/.git/*,*/.hg/*,*/.svn/*,*/tmp/cache/*,*/*.jpg,*/*.png,*/*.pyc
set wildchar=<Tab> wildmenu wildmode=full
set wildchar=<Tab> wildmenu wildmode=full

set guioptions=egm
set guifont=Bitstream_Vera_Sans_Mono:h15
set t_Co=256

if filereadable(expand("~/.vimrc_background"))
  let base16colorspace=256
  source ~/.vimrc_background
endif



" -----------------
" Text Formatting
" -----------------
set tabstop=2 softtabstop=2 shiftwidth=2 expandtab
set listchars=tab:▸\ ,eol:¬,extends:❯,precedes:❮
set showbreak=↪
set splitbelow splitright
set autowrite
set autoread
set shiftround
set title
set linebreak
highlight NonText guifg=#4a4a59
highlight SpecialKey guifg=#4a4a59
set list listchars=tab:»·,trail:.

" Don't try to highlight lines longer than 800 characters.
set synmaxcol=300

set smartindent
set foldenable
set foldlevelstart=99
set foldmethod=indent
set spl=en spell
set nospell
set hlsearch
set ignorecase
set smartcase


"""""""""""""""
""" Visuals """
"""""""""""""""

" Use relative line numbers, but show the absolute number on the current line
"set relativenumber
set number

" Show whitespace as unicode char
set listchars=tab:‣\ ,trail:\ ,extends:…,precedes:…,nbsp:˖
set list

set colorcolumn=80

set ttyfast
set lazyredraw

if has("mouse")
  set mouse=a
  set mousehide
  set ttymouse=xterm2
endif
"
" Index ctags from any project, including those outside Rails
map <Leader>ct :!ctags -R .<CR>
nnoremap <leader>. :CtrlPTag<cr>

""""""""""""""""""""""""
""" *** MAPPINGS *** """
""""""""""""""""""""""""
let mapleader = ","

" Switch between the last two files
nnoremap <leader><leader> <c-^>

noremap <Up> :GitGutterPrevHunk<CR>
noremap <Down> :GitGutterNextHunk<CR>
" Arrow Keys Navigate QuickFix Window
noremap <Right> :cnext<CR>
noremap <Left> :cprev<CR>
noremap <Leader>j :lnext<CR>
noremap <Leader>k :lprev<CR>
noremap <Leader>O :OpenChangedFiles <CR>

nnoremap n nzz
nnoremap N Nzz
nnoremap * *zz
nnoremap # #zz
nnoremap g* g*zz
nnoremap g# g#zz
"
" remap jk and kj to escape in insert mode
inoremap jk <Esc>
inoremap kj <Esc>

nnoremap <leader>n :set number!<CR>
nnoremap <leader>N :set relativenumber!<CR>

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

" bind K to grep word under cursor
"nnoremap K :grep! "\b<C-R><C-W>\b"<CR>:cw<CR>
"nmap  <silent> K :Ag <cword><CR>   
" Search for character under word
nnoremap <Leader><Leader> :Ag <cword><CR>
nnoremap \ :Ag<SPACE>
nnoremap <Leader>F :%s/\<<C-r><C-w>\>/
nnoremap <Leader>f :%s/<C-r><C-w>/

nnoremap <Leader>a :ALEToggle<cr>

" git blame shortcut
vnoremap <Leader>g :<C-U>!git blame -w <C-R>=expand("%:p") <CR> \| sed -n <C-R>=line("'<") <CR>,<C-R>=line("'>") <CR>p <CR>

vnoremap <Leader>= :Tabularize /=<cr>
vnoremap <Leader>: :Tabularize /:<cr>
vnoremap <Leader>, :Tabularize /,<cr>
vnoremap <Leader>" :Tabularize /"<cr>

"""""""""""""""""""""""""""""
""" *** AUTO COMMANDS *** """
"""""""""""""""""""""""""""""
augroup MiscMisc
  au!
  silent autocmd bufwritepost .vimrc source $MYVIMRC

  " remember fold positions
  autocmd BufWinLeave .* mkview
  autocmd BufWinEnter .* silent loadview
augroup END

" Remember last location in file
augroup RememberPosition
  au!
  au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$")
    \| exe "normal g'\"" | endif
augroup END

" Do not show cursorline on inactive panes
"augroup CursorLine
"  au!
"  au VimEnter,WinEnter,BufWinEnter * setlocal cursorline
"  au WinLeave * setlocal nocursorline
"augroup END

if has('autocmd')
  " Git
  au BufNewFile,BufRead COMMIT_EDITMSG setlocal spell!
  au BufNewFile,BufRead COMMIT_EDITMSG call feedkeys('ggi', 't')
endif

augroup NewSyntaxes
  au!
  " rabl is ruby
  au BufRead,BufNewFile *.rabl setf ruby
  au BufRead,BufNewFile *.hamlc set ft=haml
  au BufRead,BufNewFile *.skim set ft=slim
  autocmd FileType css setlocal iskeyword+=-
  autocmd FileType scss setlocal iskeyword+=-
  au BufNewFile,BufRead *.scss set ft=scss.css
augroup end

if has("persistent_undo")
  set undodir=~/.vim/undodir
  set undofile
endif

" The Silver Searcher
if executable('ag')
  set grepprg=ag\ --nogroup\ --nocolor
  let g:ctrlp_user_command = 'ag %s -l --nocolor -g ""'
  let g:ctrlp_use_caching = 0
endif

" Open new split panes to right and bottom, which feels more natural
let g:netrw_liststyle=0
let g:netrw_list_hide=netrw_gitignore#Hide()

""""""""""""""""""""""
""" Rainbow Parens """
""""""""""""""""""""""

au VimEnter * RainbowParenthesesToggle
au Syntax * RainbowParenthesesLoadRound
au Syntax * RainbowParenthesesLoadSquare
au Syntax * RainbowParenthesesLoadBraces


let g:mustache_abbreviations = 1
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

let g:EditorConfig_core_mode = 'external_command'

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
let g:ale_sign_error = '💥'
let g:ale_sign_warning = '👎'
highlight clear ALEErrorSign
highlight clear ALEWarningSign
let g:ale_echo_msg_error_str = '💥'
let g:ale_echo_msg_warning_str = '🤢'
let g:ale_echo_msg_format = '[%linter%] %s [%severity%]'

autocmd FileType javascript set formatprg=prettier\ --stdin\ --single-quote
autocmd FileType typescript :set makeprg=tsc
autocmd QuickFixCmdPost [^l]* nested cwindow
autocmd QuickFixCmdPost    l* nested lwindow

" OpenChangedFiles (<Leader>O)---------------------- {{{
function! OpenChangedFiles()
  only " Close all windows, unless they're modified
  let status = system('git status -s | grep "^ \?\(M\|A\)" | cut -d " " -f 3')
  let filenames = split(status, "\n")

  if len(filenames) < 1
    let status = system('git show --pretty="format:" --name-only')
    let filenames = split(status, "\n")
  endif

  exec "edit " . filenames[0]

  for filename in filenames[1:]
    if len(filenames) > 4
      exec "tabedit " . filename
    else
      exec "sp " . filename
    endif
  endfor
endfunction
command! OpenChangedFiles :call OpenChangedFiles()
" }}}

let loaded_bclose = 1
if !exists('bclose_multiple')
  let bclose_multiple = 1
endif

" Display an error message.
function! s:Warn(msg)
  echohl ErrorMsg
  echomsg a:msg
  echohl NONE
endfunction

" BUFFERS
nnoremap <Leader>b :ls<CR>:b<Space>
nnoremap <silent> <Leader>r :Bclose<CR>
" Command ':Bclose' executes ':bd' to delete buffer in current window.
" The window will show the alternate buffer (Ctrl-^) if it exists,
" or the previous buffer (:bp), or a blank buffer if no previous.
" Command ':Bclose!' is the same, but executes ':bd!' (discard changes).
" An optional argument can specify which buffer to close (name or number).
function! s:Bclose(bang, buffer)
  if empty(a:buffer)
    let btarget = bufnr('%')
  elseif a:buffer =~ '^\d\+$'
    let btarget = bufnr(str2nr(a:buffer))
  else
    let btarget = bufnr(a:buffer)
  endif
  if btarget < 0
    call s:Warn('No matching buffer for '.a:buffer)
    return
  endif
  if empty(a:bang) && getbufvar(btarget, '&modified')
    call s:Warn('No write since last change for buffer '.btarget.' (use :Bclose!)')
    return
  endif
  " Numbers of windows that view target buffer which we will delete.
  let wnums = filter(range(1, winnr('$')), 'winbufnr(v:val) == btarget')
  if !g:bclose_multiple && len(wnums) > 1
    call s:Warn('Buffer is in multiple windows (use ":let bclose_multiple=1")')
    return
  endif
  let wcurrent = winnr()
  for w in wnums
    execute w.'wincmd w'
    let prevbuf = bufnr('#')
    if prevbuf > 0 && buflisted(prevbuf) && prevbuf != w
      buffer #
    else
      bprevious
    endif
    if btarget == bufnr('%')
      " Numbers of listed buffers which are not the target to be deleted.
      let blisted = filter(range(1, bufnr('$')), 'buflisted(v:val) && v:val != btarget')
      " Listed, not target, and not displayed.
      let bhidden = filter(copy(blisted), 'bufwinnr(v:val) < 0')
      " Take the first buffer, if any (could be more intelligent).
      let bjump = (bhidden + blisted + [-1])[0]
      if bjump > 0
        execute 'buffer '.bjump
      else
        execute 'enew'.a:bang
      endif
    endif
  endfor
  execute 'bdelete'.a:bang.' '.btarget
  execute wcurrent.'wincmd w'
endfunction
command! -bang -complete=buffer -nargs=? Bclose call s:Bclose('<bang>', '<args>')
