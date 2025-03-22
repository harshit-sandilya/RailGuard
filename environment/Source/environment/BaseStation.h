// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

DECLARE_LOG_CATEGORY_EXTERN(LogBaseStation, Log, All);

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BaseStation.generated.h"

UCLASS()
class ENVIRONMENT_API ABaseStation : public AActor {
  GENERATED_BODY()

public:
  // Sets default values for this actor's properties
  ABaseStation();

protected:
  // Called when the game starts or when spawned
  virtual void BeginPlay() override;

public:
  // Called every frame
  virtual void Tick(float DeltaTime) override;
};
