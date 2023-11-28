from taskgraph.transforms.base import TransformSequence
from urllib.parse import urljoin
import os

CONTINUE_TRAINING_ARTIFACTS = (
    "devset.out",
    "model.npz",
    "model.npz.best-bleu-detok.npz",
    "model.npz.best-bleu-detok.npz.decoder.yml",
    "model.npz.best-ce-mean-words.npz",
    "model.npz.best-ce-mean-words.npz.decoder.yml",
    "final.model.npz.best-chrf.npz",
    "model.npz.best-chrf.npz",
    "final.model.npz.best-chrf.npz.decoder.yml",
    "model.npz.best-chrf.npz.decoder.yml",
    "model.npz.decoder.yml",
    "model.npz.optimizer.npz",
    "model.npz.progress.yml",
    "model.npz.yml",
    "train.log",
    "valid.log",
    "vocab.spm",
)

INITIALIZE_MODEL_ARTIFACTS = (
    "model.npz.best-bleu-detok.npz",
    "model.npz.best-ce-mean-words.npz",
    "final.model.npz.best-chrf.npz",
    "model.npz.best-chrf.npz",
)


def get_artifact_mount(url, directory, artifact_name):
    normalized_url = f"{url}/" if not url.endswith("/") else url
    artifact_url = urljoin(normalized_url, artifact_name)
    return {
        "content": {
            "url": artifact_url,
        },
        "file": os.path.join(directory, artifact_name),
    }


def get_artifact_mounts(urls, directory, artifact_names):
    for url in urls:
        artifact_mounts = []
        for artifact_name in artifact_names:
            artifact_mounts.append(get_artifact_mount(url, directory, artifact_name))
        yield artifact_mounts


transforms = TransformSequence()


def validate_pretrained_models(config):
    pretrained_models = config.params["training_config"]["experiment"].get("pretrained-models", {})
    train_teacher = pretrained_models.get("train-teacher")
    if train_teacher:
        teacher_ensemble = config.params["training_config"]["experiment"]["teacher-ensemble"]
        if len(train_teacher["urls"]) != teacher_ensemble:
            raise Exception(
                f"The experiment's 'teacher-ensemble' ({teacher_ensemble}) "
                f"does not match the number of provided model 'urls' ({len(train_teacher['urls'])}) "
                f"for the pretrained 'train-teacher' ensemble."
            )
    train_backwards = pretrained_models.get("train-backwards")
    if train_backwards:
        if len(train_backwards["urls"]) != 1:
            raise Exception(
                f"The experiment's 'pretrained-models.backward.urls' ({len(train_backwards['urls'])}) "
                f"must be equal to one (1). "
                f"The pipeline's backward model is _not_ an ensemble."
            )
    return pretrained_models


@transforms.add
def mount_pretrained_model_training_artifacts(config, jobs):
    pretrained_models = validate_pretrained_models(config)
    for job in jobs:
        pretrained_models_training_artifact_mounts = {
            pretrained_model: get_artifact_mounts(
                pretrained_models[pretrained_model]["urls"],
                "./artifacts",
                INITIALIZE_MODEL_ARTIFACTS
                if pretrained_models[pretrained_model]["mode"] == "init"
                else CONTINUE_TRAINING_ARTIFACTS,
            )
            for pretrained_model in pretrained_models
        }
        kind = job["task"]["tags"]["kind"]
        pretrained_model_training_artifact_mounts = next(
            pretrained_models_training_artifact_mounts.get(kind, iter((None,)))
        )
        if pretrained_model_training_artifact_mounts:
            job["task"]["payload"]["mounts"].extend(pretrained_model_training_artifact_mounts)
        yield job
