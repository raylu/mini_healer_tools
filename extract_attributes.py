import subprocess
import typing

ASSETS_DIR = 'extracted/ExportedProject/Assets/'

def extract_attributes(dotnet_script_path: str, artifacts: typing.Sequence[dict]):
	csx_path = 'extracted/ArtifactAttributes.csx'
	with open(csx_path, 'w', encoding='ascii') as f:
		write_csx(f)

		f.write('Artifact[] a = new Artifact[%d];\n' % len(artifacts))
		for i, artifact in enumerate(artifacts):
			f.write('a[%d].Key = "%s";\n' % (i, artifact['Key']))
			if artifact.get('isDivine'):
				f.write('a[%d].isDivine = true;\n' % i)
		f.write('''
Dictionary<string, List<ArtifactAttribute>> attributes = new Dictionary<string, List<ArtifactAttribute>>(a.Length);
foreach (Artifact artifact in a) {
	List<ArtifactAttribute> aa = getArtifactBaseAttributes(artifact, null);
	attributes[artifact.Key] = aa;
}
public class AttributeJsonConverter : System.Text.Json.Serialization.JsonConverter<ArtifactAttribute> {
	public override void Write(System.Text.Json.Utf8JsonWriter writer, ArtifactAttribute attr, System.Text.Json.JsonSerializerOptions options) {
		writer.WriteStartObject();
		writer.WriteString("attribute", attr.attributeType.ToString());
		writer.WriteNumber("t1_min", attr.T1_MIN);
		writer.WriteNumber("t1_max", attr.T1_MAX);
		writer.WriteBoolean("is_negative", attr.isNegative);
		writer.WriteString("ref_id", attr.refId);
		writer.WriteEndObject();
	}
	public override ArtifactAttribute Read(ref System.Text.Json.Utf8JsonReader reader, Type typeToConvert, System.Text.Json.JsonSerializerOptions options) =>
			null;
}
var serializeOptions = new System.Text.Json.JsonSerializerOptions {
    WriteIndented = true,
    Converters = { new AttributeJsonConverter() }
};
File.WriteAllText("extracted/artifact_attributes.json", System.Text.Json.JsonSerializer.Serialize(attributes, serializeOptions));
''')

	subprocess.run([dotnet_script_path, '--verbosity=e', csx_path], check=True)

def write_csx(f: typing.TextIO) -> None:
	f.write('''
public struct Artifact {
	public string Key;
	public bool isDivine;
}
public struct ArtifactSaveAttribute { public ArtifactAttribute.AddedType addedType; public ArtifactAttribute.AttriubteType attributeType; }
public class ArtifactSaveInfo { public int anomaly; public List<ArtifactSaveAttribute> SaveAttributes; }
ArtifactAttribute getBaseAttributByType(ArtifactAttribute.AttriubteType type) {
	ArtifactAttribute attr = new ArtifactAttribute();
	attr.attributeType = type;
	return attr;
}
public ArtifactAttribute getInfinityAttribute(ArtifactSaveAttribute savedAttribute) { return null; }
''')
	f.writelines(aa_lines())
	f.writelines(am_lines())

def aa_lines() -> list[str]:
	lines: list[str] = []
	with open(ASSETS_DIR + '/MonoScript/Assembly-CSharp/ArtifactAttribute.cs', 'r', encoding='ascii') as f:
		start = False
		for line in f:
			if line == '\n':
				continue
			if not start and line == 'public class ArtifactAttribute\n':
				start = True
			if start:
				if any(token in line for token in [' = ', '{', '}', 'class', 'enum']):
					lines.append(line)
				elif line.startswith('\tpublic ') and line.endswith(';\n') and \
						not any(token in line for token in ('delegate', 'DamageData', 'event')):
					lines.append(line)

	while True:
		modified = found_open = False
		for i, line in enumerate(lines):
			if line.lstrip() == '{\n':
				found_open = True
			elif found_open and line.lstrip() == '}\n':
				del lines[i]
				del lines[i - 1]
				modified = True
				break
			else:
				found_open = False
		if not modified:
			break
	return lines

def am_lines() -> list[str]:
	lines: list[str] = []
	with open(ASSETS_DIR + '/MonoScript/Assembly-CSharp/AttributesManager.cs', 'r', encoding='ascii') as f:
		start = False
		for line in f:
			if (line.startswith('\tpublic static int') or line.startswith('\tpublic static float')) \
					and line.endswith(';\n'):
				lines.append(line[1:])

			if 'getArtifactBaseAttributes' in line and 'public' in line:
				start = True
			if start:
				if line.startswith('\t\tif (saveInfo'):
					break
				lines.append(line[1:])
	lines.append('\treturn list;\n}\n')
	return lines

if __name__ == '__main__':
	import sys
	extract_attributes(sys.argv[1], [])
