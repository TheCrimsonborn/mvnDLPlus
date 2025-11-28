# mvnDLPlus

**mvnDLPlus** is a modern, future-proof Python desktop application designed to easily download Maven artifacts (JARs and POMs) directly from `mvnrepository.com` links. It features a sleek dark UI, automatic zipping, and SSL bypass capabilities.

## Features

- **Modern UI**: Built with PySide6 and a custom dark theme.
- **Smart Parsing**: Paste a `mvnrepository.com` link, and it automatically finds the download links.
- **Complete Downloads**: Automatically downloads both the `.jar` and `.pom` files.
- **Auto-Zip**: Bundles downloaded files into a single ZIP archive.
- **SSL Bypass**: Toggle to bypass SSL verification for problematic networks or sources.
- **Progress Tracking**: Real-time progress bar.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/mvnDLPlus.git
   cd mvnDLPlus
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Paste a Maven Repository link (e.g., `https://mvnrepository.com/artifact/net.sf.jasperreports/jasperreports-json/7.0.3`).

3. (Optional) Check "Bypass SSL Verification" if needed.

4. Click **Download Package**.

5. The files will be downloaded to the `downloads/` folder in the application directory.

## Requirements

- Python 3.8+
- PySide6
- Requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
