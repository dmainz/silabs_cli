Simplicity Studio 6 Installation Info

All tools, SDKs, etc. are installed in: \<user\_home\>/.silabs

Files of most interest in this directory are:

sdks.json – describes which SDKs are installed and where.  Look here first to find SDK info.

tools.json – describes which tools are installed and where.  Look here first to find tool info.

slt – the folder that holds all installed SDKs and tools.

slt/slt.location – the path to the slt executable.  Use this to make scripts relocatable.

slt/installs/archive has the simplicity tools such as commander, slc-cli, etc. Refer to tools.json for info.

slt/installs/conan has the SDK and tool folders.

slt/installs/conan/p has the installed SDK folders.  Refer to sdks.json and tools.json to get info on each folder.

slt/installs/conan/p/\<sdk\_folder\>/p has all the SDK related files.

The preferred SDK is 2025.12.1.

The following tools/SDKs are not currently of interest: aiml, matter\_extension, sidewalk, wiseconnect, aox.

We will be using slt-cli, slc-cli, and commander extensively for project creation, configuration, building, flashing, and to some degree, debugging.  Refer to tools.json for slt-cli and slc-cli locations.

Some SDK files with information about the components and examples within the SDK directory are:

\<sdk\_folder\>/p/conanmanifest.txt

\<sdk\_folder\>/p/simplicity\_sdk.slcs

\<sdk\_folder\>/p/toolchains.slct

where \<sdk\_folder\> is \<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399.  Refer to sdks.json for SDK location.

Simplicity platform related examples are in:

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/platform\_sample\_app/app/common/example

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/platform\_common\_apps/app/common/example

Other example folders of interest are:

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/bluetooth\_le\_app/example

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/rail\_sdk\_sample\_app/documentation/example

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/rail\_sdk\_sample\_app/example

\<user\_home\>/.silabs/slt/installs/conan/p/simpl1a11563c2e399/p/platform\_security\_sample\_app/app/common/example

Command line development documentation is here: [https://docs.silabs.com/command-line-development/latest/ssv6-command-line-development/](https://docs.silabs.com/command-line-development/latest/ssv6-command-line-development/)

SLT-CLI documentation is here: [https://docs.silabs.com/command-line-development/latest/ssv6-slt-cli/slt-configuration](https://docs.silabs.com/command-line-development/latest/ssv6-slt-cli/slt-configuration)

SLC-CLI documentation his here: [https://docs.silabs.com/command-line-development/latest/ssv6-slc-cli/use-slc-cli](https://docs.silabs.com/command-line-development/latest/ssv6-slc-cli/use-slc-cli)

