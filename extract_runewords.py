import subprocess
import typing

import extract_attributes

ASSETS_DIR = 'extracted/ExportedProject/Assets/'

def extract_runewords(dotnet_script_path: str):
	csx_path = 'extracted/Runewords.csx'
	with open(csx_path, 'w', encoding='ascii') as f:
		write_csx(f)

		f.write(extract_attributes.ATTRIBUTE_JSON_CONVERTER)
		f.write('''
SocketDataController.RefreshRunewordData();
public class RunewordJsonConverter : System.Text.Json.Serialization.JsonConverter<Runeword> {
	public override void Write(System.Text.Json.Utf8JsonWriter writer, Runeword rw, System.Text.Json.JsonSerializerOptions options) {
		writer.WriteStartObject();
		writer.WriteString("title", rw.title);

		writer.WriteStartArray("rune_key");
		foreach (string rune in rw.runeKey)
			writer.WriteStringValue(rune);
		writer.WriteEndArray();

		writer.WriteEndObject();
	}
	public override Runeword Read(ref System.Text.Json.Utf8JsonReader reader, Type typeToConvert, System.Text.Json.JsonSerializerOptions options) =>
			null;
}
var serializeOptions = new System.Text.Json.JsonSerializerOptions {
    WriteIndented = true,
    Converters = { new AttributeJsonConverter(), new RunewordJsonConverter() }
};
File.WriteAllText("extracted/runewords.json", System.Text.Json.JsonSerializer.Serialize(runeWords, serializeOptions));
''')

	subprocess.run([dotnet_script_path, '--verbosity=e', csx_path], check=True)

def write_csx(f: typing.TextIO) -> None:
	f.write('''
public class Artifact {
	public enum ArtifactSlotType {
		WEAPON = 0, ARMOR = 1, ACCESSORY = 2,
		CHAOS = 3, MAP = 4, TAROT = 5,
		GEM = 6, KEY = 7, DEPTH_INFUSEABLE = 8,
	}
}
public class Runeword {
	public Runeword() {}
	public Runeword(string[] _runeKeys) {
		runeKey = _runeKeys;
	}
	public string getRuneKeyString() {
		return string.Join("", runeKey);
	}
	public string[] runeKey;
	public string title;
	public List<ArtifactAttribute> attributes;
	public List<string> specialDesc;
	public Artifact.ArtifactSlotType slotType;
}
private static string getRunewordsName(string wordKey) { return null; }
private static List<ArtifactAttribute> getRunewordsAttributes(string word) { return null; }
private static List<string> getRunewordsSpecialDesc(string wordKey) { return null; }
private static Runeword getRunewordEffect(Runeword runeword) { return runeword; }
static List<Runeword> runeWords = new List<Runeword>();
''')
	f.writelines(extract_attributes.aa_lines())
	f.writelines(sdc_lines())

def sdc_lines() -> list[str]:
	lines  = ['public class SocketDataController {\n']
	with open(ASSETS_DIR + '/MonoScript/Assembly-CSharp/SocketDataController.cs', 'r', encoding='ascii') as f:
		in_func = False
		for line in f:
			if line == '\n':
				continue

			if not in_func and ('void RefreshRunewordData()' in line or 'string getRunewordsName' in line):
				in_func = True
			if ('static Runeword ' in line and 'new Runeword' in line) or in_func:
				lines.append(line)
			if in_func and line == '\t}\n':
				in_func = False
	lines.append('}')
	return lines

if __name__ == '__main__':
	import sys
	extract_runewords(sys.argv[1])
