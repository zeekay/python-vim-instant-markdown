if !has('python')
    echo "Error: Required vim compiled with +python"
    finish
endif

let s:scriptfolder = expand('<sfile>:p:h').'/md_instant'

function! OpenMarkdown()
    au CursorMoved,CursorMovedI,CursorHold,CursorHoldI <buffer> silent call UpdateMarkdown()
    au BufWinLeave <buffer> silent call CloseMarkdown()
    let b:md_tick = ""
python << EOF
import sys, os, vim, time

for lib in ['pygments', 'markdown']:
    try:
        __import__(lib)
    except:
        vim.command('!pip install ' + lib)
        vim.command('redraw!')

sys.path.append(vim.eval('s:scriptfolder'))
sys.stdout = open(os.path.devnull, 'w')
sys.stderr = open(os.path.devnull, 'w')
import md_instant
md_instant.main(vim.current.buffer)
md_instant.startbrowser()
EOF
    redraw!
endfunction

function! UpdateMarkdown()
    if (b:md_tick != b:changedtick)
        let b:md_tick = b:changedtick
python << EOF
md_instant.sendall(vim.current.buffer)
EOF
    endif
endfunction
function! CloseMarkdown()
python << EOF
md_instant.stopserver()
EOF
endfunction

au FileType markdown command! -nargs=0 Preview call OpenMarkdown()
