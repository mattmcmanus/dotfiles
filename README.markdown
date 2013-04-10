# mattmcmanus dotfiles

Dotfiles are the best. This repo includes tons of tweaks and settings. 

* Lots of helpful scripts (for me) in `bin`
* The most amazing collection of osx related config changes in `osx`
* Lots of bash tweaks in `system`
* Configuration for `git`, `tmux` and `vim`

## install

Run this:

```sh
git clone https://github.com/mattmcmanus/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
script/bootstrap
```

This will symlink the appropriate files in `.dotfiles` to your home directory.
Everything is configured and tweaked within `~/.dotfiles`, though.

You'll also want to change `git/gitconfig.symlink`, which will set you up as committing as me. You probably don't want that.


## Thanks


This originally started as a fork of [Zach Holman](http://github.com/holman)'s 
[dotfiles](http://github.com/holman/dotfiles). It was an excellent place to learn many interesting tweaks. I've yet to convert to ZSH so my fork diverged a lot so I eventually made my own. Many of the scripts and some of the files are still straight up copies of his. 
