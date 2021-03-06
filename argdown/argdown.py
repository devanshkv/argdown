import argparse as _argparse
# table col
import os as _os
# output
import textwrap as _textwrap

version = '1.1.0'
cols = _os.environ['COLUMNS'] if 'COLUMNS' in _os.environ else 78


def md_help(parser, *, depth=1, header='Arguments and Usage',
            usage_header='Usage', ref_header='Quick reference table',
            args_header='Arguments', spacey=False, show_default=True,
            truncate_help=True, rst=False, hierarchy='#=-*+.', tiny=False, outfile=None):
    def code_block(code):
        if rst:
            out = '\n::\n\n'
            for line in code.split('\n'):
                out += f'    {line}\n'
            out += '\n'
            return out
        else:
            return f'```\n{code}```\n'

    def header_text(text, depth):
        if rst:
            return (text
                    + '\n' + hierarchy[depth - 1] * len(text)
                    + f'\n{space}')
        else:
            return '#' * depth + f' {text}\n{space}'

    def options_table(opts):
        # table divider character
        d = '|'

        if not rst:
            options.insert(1, {
                'short': '-' * table_widths.short,
                'long': '-' * table_widths.long,
                'default': '-' * table_widths.default,
                'help': '-' * table_widths.help,
            })

        divider_line = ('+'
                        + '-' * table_widths.short + '+'
                        + '-' * table_widths.long + '+'
                        + '-' * table_widths.default + '+'
                        + '-' * table_widths.help + '+\n'
                        ) if rst else ''
        table = divider_line

        for opt in options:
            table += (
                         f'{d}{{short:{table_widths.short}}}{d}'
                         f'{{long:{table_widths.long}}}{d}'
                         f'{{default:{table_widths.default}}}{d}'
                         f'{{help:{table_widths.help}.{table_widths.help}}}{d}\n'
                     ).format(**opt) + divider_line
        return table

    # inline code delimiter
    icd = '``' if rst else '`'

    def inline_code(code):
        return f'{icd}{code}{icd}'

    global cols
    space = '\n' if spacey else ''
    if not tiny:
        out = (header_text(header, depth)
               + header_text(usage_header, depth + 1)
               + code_block(parser.format_usage())
               + header_text(args_header, depth + 1)
               + header_text(ref_header, depth + 2))
    else:
        out = (code_block(parser.format_usage()) + header_text('Arguments', depth + 2))

    used_actions = {}
    args_detailed = ''

    options = []

    class TableWidths():
        def __init__(self, **kwargs):
            for key, val in kwargs.items():
                setattr(self, key, val)

        def maximize(self, key, val):
            setattr(self, key, max(getattr(self, key), len(val)))

    table = ''
    table_widths = TableWidths(
        short=len('Short'),
        long=len('Long'),
        default=len('Default'),
        help=0
    )

    i = 0
    for k in parser._option_string_actions:
        action = parser._option_string_actions[k]
        this_id = id(action)
        if this_id in used_actions:
            continue
        used_actions[this_id] = True

        options.append({
            'long': '',
            'short': '',
            'default': '',
            'help': action.help
        })

        for opt in action.option_strings:
            # --, long option
            if len(opt) > 1 and opt[1] in parser.prefix_chars:
                options[i]['long'] = inline_code(opt)
                table_widths.maximize('long', options[i]['long'])
            # short opt
            elif len(opt) > 0 and opt[0] in parser.prefix_chars:
                options[i]['short'] = inline_code(opt)
                table_widths.maximize('short', options[i]['short'])

        # don't show defaults for options
        default_str = ''
        if (show_default and
                not (isinstance(action.default, bool)
                     or isinstance(action, _argparse._VersionAction)
                     or isinstance(action, _argparse._HelpAction))):
            default = action.default if isinstance(action.default, str) else repr(action.default)
            options[i]['default'] = inline_code(default)
            table_widths.maximize('default', options[i]['default'])
            default_str = f' (Default: {default})'

        table_widths.maximize('help', action.help)

        args_detailed += (header_text(
            inline_code(f'{icd}, {icd}'.join(action.option_strings))
            + default_str, depth + 2)
                          + _textwrap.fill(action.help, width=cols) + '\n\n')
        i += 1

    # with proper lengths, we can make the table
    if truncate_help:
        table_widths.help = (cols
                             - table_widths.short
                             - table_widths.long
                             - table_widths.default
                             - 4)

    # table headers
    options.insert(0, {
        'short': 'Short',
        'long': 'Long',
        'default': 'Default',
        'help': 'Description'
    })
    if not tiny:
        out += options_table(options) + '\n' + args_detailed
    else:
        out += options_table(options)

    if outfile is None:
        return out
    else:
        print("writing out to ", outfile)
        with open(outfile, 'w') as f:
            f.write(out)


def console():
    prog = 'argdown'
    global cols

    argparser = _argparse.ArgumentParser(
        description='Markdown export for the argparse module',
        prog=prog,
        epilog=
        '''Argdown requires a fully formed ArgumentParser object, after all the
        add_argument()s have been executed. The only way to make sure the
        ArgumentParser object is created in the same way that it would be during normal
        script execution is to execute the script until the arguments are parsed. To do
        this, argdown reads the input file(s) from `ArguementPaeser(` until it reads a line
        containing `.parse_args(`. The rest of the file, being irrelevant to the command-line
        invocation, is truncated, and a call to `argdown.md_help()` is inserted to
        generate the Markdown from the parser. Now the script between `ArguementPaeser(`
        and `parse_args` is executed in its entirety, including any side-effects that may
        entail --- argdown does not attempt to sanitize the code in any way.

        More info: github.com/devanshkv/argdown''')

    argparser.add_argument('src_file', nargs='+',
                           help='The filename of a Python file to export Markdown from.')

    argparser.add_argument('-', action='store_true', dest='use_stdin',
                           help='Read from STDIN instead of a file.')

    argparser.add_argument('--header', type=str,
                           default='Arguments and Usage',
                           help='Header text for the `Arguments and Usage` section.')

    argparser.add_argument('--usage-header', type=str, default='Usage',
                           help='Header text for the `Usage` section.')

    argparser.add_argument('--ref-header', type=str, default='Quick '
                                                             'reference table',
                           help='Header text for the `Quick reference '
                                'table` section, a simple table of all the arguments.')

    argparser.add_argument('--args-header', type=str,
                           default='Arguments', help='Header text for the `Arguments` '
                                                     'section, a detailed listing of all the arguments.')

    argparser.add_argument('-s', '--spacey', action='store_true',
                           help='Output a blank line after headers.')

    argparser.add_argument('-r', '--rst', action='store_true',
                           help='Generate rst (reStructured Text) instead of Markdown.')

    argparser.add_argument('-e', '--hierarchy', type=str,
                           default='#=-*+.',
                           help='Order of header characters to use for rst output.')

    argparser.add_argument('-d', '--hide-default', action='store_true',
                           help='Don\'t output default values for the arguments.')

    argparser.add_argument('-t', '--truncate-help', action='store_true',
                           help='Truncate help in the `Quick reference table` section so that '
                                'the table\'s width doesn\'t exceed `--width`. Makes terminal output '
                                'prettier but means you\'ll probably have to re-write help messages.')

    argparser.add_argument('--header-depth', type=int, default=1,
                           help='Header depth; number of hashes to output before the '
                                'top-level header.')

    argparser.add_argument('--encoding', type=str, default='utf-8',
                           help='Encoding of all input files. Frankly, there\'s no excuse to '
                                'ever use this argument')

    argparser.add_argument('-f', '--function', type=str,
                           help='Function to be called to parse args. For example, if the '
                                'arg-parsing mechanism is contained in a `console()` function '
                                '(common if the script is a module and has a console entry point '
                                'defined), enter `--function console` if `console()` must be called '
                                'to define the argument parser.')

    argparser.add_argument('-v', '--version', action='version',
                           version=f'%(prog)s {version}')

    argparser.add_argument('--tiny', action='store_true', help='Make only the usage table')

    argparser.add_argument('-o', '--output', help='save in the output file', type=str, required=False, nargs=1)

    args = argparser.parse_args()

    header = args.header
    usage_header = args.usage_header
    ref_header = args.ref_header
    args_header = args.args_header
    spacey = args.spacey
    show_default = not args.hide_default
    truncate_help = args.truncate_help
    depth = args.header_depth
    function = args.function
    use_rst = args.rst
    be_tiny = args.tiny
    if args.output:
        out_file = str(args.output[0])
    else:
        out_file = None

    import re

    def get_indent(line):
        indent = 0
        for c in line:
            if c == ' ':
                indent += 1
            elif c == '\t':
                indent += 8
            else:
                # break on first word / non-white char
                break
        return indent

    def gen_help(src):
        lines = src.split('\n')
        indent = 0
        startline = 0
        lastline = len(lines)
        end_parser_expr = re.compile(r'(\w+)\.parse_args\(')
        start_parser_exper = re.compile(r'(\w+)\.ArgumentParser\(')
        for i, line in enumerate(lines):
            if '.ArgumentParser(' in line:
                parser = re.search(start_parser_exper, line)
                if parser is not None:
                    startline = i
                    indent = get_indent(line)
                    parser = parser.group(1)
            elif '.parse_args(' in line:
                parser = re.search(end_parser_expr, line)
                if parser is not None:
                    lastline = i
                    parser = parser.group(1)
                    # indent = get_indent(line)
                    break
        lines = lines[startline:lastline]
        lines.insert(0, 'import argdown, argparse')
        if indent > 0:
            lines.insert(1, "if __name__ == '__main__':")
        lines.append(' ' * indent +
                     f'print(argdown.md_help({parser}, depth={depth},\n'
                     f'header=\'{header}\', usage_header=\'{usage_header}\',\n'
                     f'ref_header=\'{ref_header}\', args_header=\'{args_header}\',\n'
                     f'spacey={spacey}, show_default={show_default},\n'
                     f'truncate_help={truncate_help}, rst={use_rst} , tiny={be_tiny}, outfile="{out_file}"))')
        if function is not None:
            lines.append(function + '()')
        exec('\n'.join(lines), {'__name__': '__main__'})

    if args.use_stdin:
        # catenate stdinput, parse / render
        src = ''
        for line in sys.stdin:
            src += line + '\n'
        gen_help(src)
        exit()

    # process each file, respecting encoding, although i really hope nobody
    # ever uses that argument and to be quite frank i haven't tested it
    for fname in args.src_file:
        with open(fname, 'r', encoding=args.encoding) as f:
            gen_help(f.read())