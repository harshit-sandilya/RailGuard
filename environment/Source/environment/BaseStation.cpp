// Fill out your copyright notice in the Description page of Project Settings.

#include "BaseStation.h"
DEFINE_LOG_CATEGORY(LogBaseStation);

// Sets default values
ABaseStation::ABaseStation() {
  // Set this actor to call Tick() every frame.  You can turn this off to
  // improve performance if you don't need it.
  PrimaryActorTick.bCanEverTick = true;
}

// Called when the game starts or when spawned
void ABaseStation::BeginPlay() {
  Super::BeginPlay();
  UE_LOG(LogBaseStation, Warning, TEXT("BaseStation BeginPlay() called"));
}

// Called every frame
void ABaseStation::Tick(float DeltaTime) { Super::Tick(DeltaTime); }
