import enum
import subprocess
import typing

ASSETS_DIR = 'extracted/ExportedProject/Assets/'

def extract_descriptions(dotnet_script_path:str, artifacts: typing.Sequence[dict]):
	csx_path = 'extracted/ArtifactDescriptions.csx'
	with open(csx_path, 'w', encoding='ascii') as f:
		write_csx(f)

		f.write('Artifact[] a = new Artifact[%d];\n' % len(artifacts))
		for i, artifact in enumerate(artifacts):
			for k, v in artifact.items():
				if isinstance(v, list):
					continue
				elif isinstance(v, float):
					v = str(v) + 'f'
				elif isinstance(v, str):
					v = '"%s"' % v
				elif isinstance(v, bool):
					v = str(v).lower()
				elif not isinstance(v, int):
					raise AssertionError('unexpected type %s for %r %r' % (type(v), artifact['Key'], k))
				f.write('a[%d].%s = %s;\n' % (i, k, v))
		f.write('''
Dictionary<string, List<string>> descriptions = new Dictionary<string, List<string>>(a.Length);
static bool EmptyDesc(string s) { return s == "" || s == " "; }
foreach (Artifact artifact in a) {
	List<string> desc = getDescriptionByArtifact(artifact, 15, false);
	desc.RemoveAll(EmptyDesc);
	descriptions[artifact.Key] = desc;
}
File.WriteAllText("extracted/artifact_descriptions.json", System.Text.Json.JsonSerializer.Serialize(descriptions));
''')

	subprocess.run([dotnet_script_path, '--verbosity=e', csx_path], check=True)

def write_csx(f: typing.TextIO) -> None:
	f.write('''
public struct Artifact {
	public string ArtifactName;
	public string Key;
	public bool isAugmentable;
	public bool isChaotic;
	public bool isCorrupted;
	public bool isDepth;
	public bool isDiscoverable;
	public bool isDivine;
	public bool isEquippable;
	public bool isMutateable;
	public bool isUltraRare;
	public bool useImgResourcePath;
	public List<int> artifactVFXSpawnType;
	public string VFXResourceName;
	public int Rarity;
	public int SlotType;
	public int Type;
	public int maxAnomaly;
	public List<int> MutationPoolType;
	public int HiddenItemLevel;
	public int procCooldown;
	public int procCooldownRemaining;
	public bool hasInitialProcCooldown;
	public float DropRate;
	public int difficulty;
	public List<int> possibleMutationAttributes;
	public List<int> possibleRolledAttributes;
	public int minEleDmgMod;
	public int maxEleDmgMod;
	public int minEleResistMod;
	public int maxEleResistMod;
	public int eleResistTier;
	public int eleResistTierce;
	public string specialDesc;
	public string PurchaseMat;
	public int PurchasePrice;
}
public class ArtifactSaveInfo { public int anomaly; }
public class DamageData {
	public enum DamageElement {
		Physical = 0,
		Fire = 1,
		Ice = 2,
		Lightning = 3,
		Nemesis = 4,
	}
}
class LocalizedString {
	public LocalizedString(string name) {
		this.localizedString = name;
	}
	public string localizedString;
}
class UtilsManager { public static string addHoverTooltip(string s, bool addHoverTooltip) { return s; } }
class Mathf {
	public static int RoundToInt(float f) {
		return (int)System.Math.Round(f);
	}
}
''')
	f.writelines(adc_lines())
	f.writelines(am_lines())
	f.writelines(ogdc_class_lines())
	f.write('static OtherGameDataController GDM = new OtherGameDataController();\n')
	f.writelines(ogdc_dba_lines())

def adc_lines() -> list[str]:
	lines = ['''
public class ArtifactDataController {
	public static float getQualityDeltaFloat(float min, float max, int quality)
	{
		return (float)System.Math.Round((min + (max - min) * ((float)quality / (float)OtherGameDataController.MaxQuality)) * 100f) / 100f;
	}
''']
	with open(ASSETS_DIR + '/MonoScript/Assembly-CSharp/ArtifactDataController.cs', 'r', encoding='ascii') as f:
		lines.extend(extract_static_consts(f))
	lines.append('}\n')
	return lines

def am_lines() -> list[str]:
	lines = ['public class AttributesManager {\n']
	with open(ASSETS_DIR + '/MonoScript/Assembly-CSharp/AttributesManager.cs', 'r', encoding='ascii') as f:
		lines.extend(extract_static_consts(f))
	lines.append('}\n')
	return lines

def ogdc_class_lines() -> list[str]:
	lines = ['class OtherGameDataController {\n']
	with open(ASSETS_DIR + 'MonoScript/Assembly-CSharp/OtherGameDataController.cs', 'r', encoding='ascii') as f:
		lines.extend(extract_static_consts(f))
	lines.append('''
public string getElementTextByElementType(DamageData.DamageElement element)
{
	string inputStr = "CONTEXT_ELEMENT_PHYSICAL";
	switch (element)
	{
	case DamageData.DamageElement.Physical:
		inputStr = "CONTEXT_ELEMENT_PHYSICAL";
		break;
	case DamageData.DamageElement.Fire:
		inputStr = "CONTEXT_ELEMENT_FIRE";
		break;
	case DamageData.DamageElement.Ice:
		inputStr = "CONTEXT_ELEMENT_ICE";
		break;
	case DamageData.DamageElement.Lightning:
		inputStr = "CONTEXT_ELEMENT_LIGHTNING";
		break;
	case DamageData.DamageElement.Nemesis:
		inputStr = "CONTEXT_ELEMENT_NEMESIS";
		break;
	}
	return new LocalizedString(inputStr).localizedString;
}
''')
	lines.append('}\n')
	return lines

class State(enum.Enum):
	OUTSIDE = enum.auto()
	FOUND_DEF = enum.auto()
	OPENING_BRACE = enum.auto()
	INSIDE = enum.auto()
	FOUND_SPECIAL_DESC = enum.auto()
def ogdc_dba_lines() -> list[str]:
	lines: list[str] = []
	with open(ASSETS_DIR + 'MonoScript/Assembly-CSharp/OtherGameDataController.cs', 'r', encoding='ascii') as f:
		state = State.OUTSIDE
		for line in f:
			if state == State.OUTSIDE:
				if 'getDescriptionByArtifact(' in line:
					state = State.FOUND_DEF
			elif state == State.FOUND_DEF:
				assert line == '	{\n'
				state = State.OPENING_BRACE
			elif state == State.OPENING_BRACE:
				state = State.INSIDE
			if state == State.INSIDE:
				if 'artifact.specialDesc' in line:
					state = State.FOUND_SPECIAL_DESC

			if state in (State.FOUND_DEF, State.OPENING_BRACE, State.FOUND_SPECIAL_DESC) or \
					(state == State.INSIDE and 'list = new' in line):
				lines.append(line[1:])

			if state == State.FOUND_SPECIAL_DESC:
				if line == '	}\n':
					break
	return lines

def extract_static_consts(f: typing.TextIO) -> typing.Generator[str, None, None]:
	accepted_types = ['float', 'int', 'bool']
	for line in f:
		if (line.startswith('\tpublic static ') or line.startswith('\tprivate static ')) \
				and line.endswith(';\n') and any(t in line for t in accepted_types):
			yield line

if __name__ == '__main__':
	import sys
	extract_descriptions(sys.argv[1], [])
