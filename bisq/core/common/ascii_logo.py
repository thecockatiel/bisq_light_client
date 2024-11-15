 
from bisq.log_setup import get_logger


logger =  get_logger(__name__)

class AsciiLogo:
    @staticmethod
    def show_ascii_logo():
        ascii_art = "\n\n" \
                    "                    ........                  ......                                                                         \n" \
                    "                ..............                ......                                                                         \n" \
                    "              .................               ......                                                                         \n" \
                    "            ......   ..........   ..          ......                                                                         \n" \
                    "           ......      ......   ......        ...............        .....     .........         ..........                  \n" \
                    "          .......              ........       ..................     .....   .............     ...............               \n" \
                    "          ......               ........       ..........  .......    .....  ......   ...     ........   .......              \n" \
                    "         ......                   .....       .......        .....   .....  .....            .....        ......             \n" \
                    "         ......    ...        ...             ......         ......  .....   ...........    ......         ......            \n" \
                    "         ......   .....      ....             ......         ......  .....    ............  .....          ......            \n" \
                    "          ......                               .....         ......  .....         ........ ......         ......            \n" \
                    "           ......       ....        ...        ......       ......   .....    ..     ......  ......      ........            \n" \
                    "            ........     ..      .......        .................    .....  ..............    ...................            \n" \
                    "             ..........       .........           .............      .....   ............       .................            \n" \
                    "               ......................                 .....                      ....               ....   ......            \n" \
                    "                  ................                                                                         ......            \n" \
                    "                        ....                                                                               ......            \n" \
                    "                                                                                                           ......            \n" \
                    "\n\n"
        logger.info(ascii_art)