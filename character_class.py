from dataclasses import dataclass, field

@dataclass
class myCharacter:
    race: str="",
    subrace: str="",
    strength: int=0,
    dexterity: int=0,
    constitution: int=0,
    intelligence: int=0,
    wisdom: int=0,
    charisma: int=0,
    speed: int=0,
    vision: int=0,
    HP: int=0,
    tools: list=field(default_factory=list),
    spells: list=field(default_factory=list),
    skills: list=field(default_factory=list),
    languages: list=field(default_factory=list),
    combat: list=field(default_factory=list),
    misc: list=field(default_factory=list),
