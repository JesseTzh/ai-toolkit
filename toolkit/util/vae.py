from diffusers import AutoencoderKL


def load_vae(vae_path, dtype, local_files_only=False):
    try:
        vae = AutoencoderKL.from_pretrained(
            vae_path,
            torch_dtype=dtype,
            local_files_only=local_files_only,
        )
    except Exception as e:
        try:
            vae = AutoencoderKL.from_pretrained(
                vae_path,
                subfolder="vae",
                torch_dtype=dtype,
                local_files_only=local_files_only,
            )
        except Exception as e:
            raise ValueError(f"Failed to load VAE from {vae_path}: {e}")
    vae.to(dtype)
    return vae
