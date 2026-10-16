from dataclasses import dataclass, field

@dataclass
class Character:
    race: str=""
    subrace: str=""
    strength: int=0
    dexterity: int=0
    constitution: int=0
    intelligence: int=0
    wisdom: int=0
    charisma: int=0
    speed: int=0
    vision: int=0
    HP: int=0
    tool_profs: list=field(default_factory=list)
    weapon_profs: list=field(default_factory=list)
    spells: list=field(default_factory=list)
    skills: list=field(default_factory=list)
    languages: list=field(default_factory=list)
    race_misc: list=field(default_factory=list)

    dnd_class: str=""
    hit_dice: str=""
    saving_throws: list=field(default_factory=list)
    class_misc: list=field(default_factory=list)
    equipment: list=field(default_factory=list)
    cantrips: list=field(default_factory=list)
    spells: list=field(default_factory=list)
