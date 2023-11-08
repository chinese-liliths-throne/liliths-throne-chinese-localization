package com.lilithsthrone.game.character.gender;

/**
 * @since 0.1.86
 * @version 0.1.97
 * @author Innoxia
 */
public enum GenderNames {

	Y_PENIS_Y_VAGINA_Y_BREASTS(true, true, true, "futanari", "hermaphrodite", "hermaphrodite", "扶她", "双性人", "双性人"),
	Y_PENIS_Y_VAGINA_N_BREASTS(true, true, false, "futanari", "hermaphrodite", "hermaphrodite", "扶她", "双性人", "双性人"),
	Y_PENIS_N_VAGINA_Y_BREASTS(true, false, true, "shemale", "shemale", "busty-boy", "人妖", "人妖", "胸男"),
	Y_PENIS_N_VAGINA_N_BREASTS(true, false, false, "trap", "trap", "male", "伪娘", "伪娘", "男性"),
	N_PENIS_Y_VAGINA_Y_BREASTS(false, true, true, "female", "tomboy",  "butch", "女性", "假小子",  "女汉子"),
	N_PENIS_Y_VAGINA_N_BREASTS(false, true, false, "female", "tomboy", "cuntboy", "女性", "假小子", "穴男"),
	N_PENIS_N_VAGINA_Y_BREASTS(false, false, true, "mannequin", "neuter", "mannequin", "石女", "中性人", "石男"),
	N_PENIS_N_VAGINA_N_BREASTS(false, false, false, "mannequin", "neuter", "mannequin", "石女", "中性人", "石男");
	
	
	private boolean hasPenis, hasVagina, hasBreasts;
	private String feminine, masculine, neutral, feminineId, masculineId, neutralId;
	
	private GenderNames(boolean hasPenis, boolean hasVagina, boolean hasBreasts, String feminineId, String neutralId, String masculineId, String feminine, String neutral, String masculine){
		this.hasPenis = hasPenis;
		this.hasVagina = hasVagina;
		this.hasBreasts = hasBreasts;
		this.feminine = feminine;
		this.neutral = neutral;
		this.masculine = masculine;
		this.feminineId = feminineId;
		this.masculineId = masculineId;
		this.neutralId = neutralId;
	}

	public boolean isHasPenis() {
		return hasPenis;
	}

	public boolean isHasVagina() {
		return hasVagina;
	}

	public boolean isHasBreasts() {
		return hasBreasts;
	}
	
	public String getFeminine() {
		return feminine;
	}

	public String getMasculine() {
		return masculine;
	}

	public String getNeutral() {
		return neutral;
	}

	public String getFeminineId() {
		return feminineId;
	}

	public String getMasculineId() {
		return masculineId;
	}

	public String getNeutralId() {
		return neutralId;
	}
}
