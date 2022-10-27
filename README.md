## setup

install AssetRipper console: https://assetripper.github.io/AssetRipper/articles/Downloads.html
install dotnet: https://dotnet.microsoft.com/download

```sh
$ dotnet tool install -g dotnet-script
$ pip3 install -r requirements.txt
$ ln -s '/mnt/.../Steam/steamapps/common/Mini Healer/MiniHealer_Data/' raw
$ ./extract.py path/to/AssetRipperConsole ~/.dotnet/tools/dotnet-script
```

hit enter once you see `Export : Finished post-export`
