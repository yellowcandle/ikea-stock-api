{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.setuptools
    pkgs.python312Packages.wheel
    pkgs.chromium  # For selenium
    pkgs.chromedriver  # For selenium
    pkgs.firefox  # Alternative browser
    pkgs.geckodriver  # Firefox driver
    pkgs.xvfb-run  # Virtual framebuffer for headless browser
    pkgs.which  # Required for webdriver-manager
    pkgs.gcc  # For compiling some Python packages
    pkgs.libffi  # Common dependency
    pkgs.openssl  # For secure connections
    pkgs.zlib  # Compression library
  ];
  env = {
    PYTHONBIN = "${pkgs.python312}/bin/python3.12";
    LANG = "en_US.UTF-8";
    PYTHONIOENCODING = "utf-8";
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.libffi
      pkgs.openssl
      pkgs.zlib
    ];
    CHROME_BIN = "${pkgs.chromium}/bin/chromium";
    CHROMEDRIVER_PATH = "${pkgs.chromedriver}/bin/chromedriver";
  };
}
