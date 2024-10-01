#!/usr/bin/perl
use strict;
use warnings;
use threads;
use Time::HiRes qw(sleep);
use Math::Random qw(rand);
use JSON; # to_json function used for JSON data
use MinIO::Client;

# Configuration Constants
use constant {
    MINIO_ENDPOINT   => "localhost:9000",
    MINIO_ACCESS_KEY => "your_access_key",
    MINIO_SECRET_KEY => "your_secret_key",
    BUCKET_NAME      => "game-of-life-patterns",
    GRID_SIZE        => 100,
    NUM_THREADS      => 16,
    DENSITY          => 0.1,
    MAX_ITERATIONS   => 100,
};

# Global MinIO Client Initialization
my $minio_client = MinIO::Client->new(
    endpoint   => MINIO_ENDPOINT,
    access_key => MINIO_ACCESS_KEY,
    secret_key => MINIO_SECRET_KEY,
    secure     => 0,
);

# Ensure bucket exists
unless ($minio_client->bucket_exists(BUCKET_NAME)) {
    $minio_client->make_bucket(BUCKET_NAME) or die "Failed to create bucket: $!";
}

# SparseGrid class definition
package SparseGrid;
sub new {
    my $class = shift;
    return bless { grid => {} }, $class;
}

sub get {
    my ($self, $x, $y) = @_;
    return exists $self->{grid}{"$x,$y"} ? 1 : 0;
}

sub set {
    my ($self, $x, $y, $value) = @_;
    if ($value) {
        $self->{grid}{"$x,$y"} = 1;
    } else {
        delete $self->{grid}{"$x,$y"};
    }
}

sub count {
    my $self = shift;
    return scalar keys %{ $self->{grid} };
}

# Calculate next state based on Game of Life rules
sub calculate_next_state {
    my ($grid, $x, $y) = @_;
    my $live_neighbours = 0;
    
    for my $dx (-1, 0, 1) {
        for my $dy (-1, 0, 1) {
            next if ($dx == 0 && $dy == 0);
            my $nx = $x + $dx;
            my $ny = $y + $dy;
            $live_neighbours++ if ($grid->get($nx, $ny));
        }
    }

    return ($grid->get($x, $y) && ($live_neighbours == 2 || $live_neighbours == 3)) || (!$grid->get($x, $y) && $live_neighbours == 3) ? 1 : 0;
}

sub generate_initial_conditions {
    my ($grid) = @_;
    for my $y (0 .. GRID_SIZE - 1) {
        for my $x (0 .. GRID_SIZE - 1) {
            $grid->set($x, $y, rand() <= DENSITY ? 1 : 0);
        }
    }
}

# The thread function for updating the grid
sub update_grid_thread {
    my ($grid, $thread_id) = @_;
    my $chunk_size = int(GRID_SIZE / NUM_THREADS);

    while (1) {
        my $start_y = $chunk_size * ($thread_id - 1);
        my $end_y = $thread_id == NUM_THREADS ? GRID_SIZE - 1 : $start_y + $chunk_size - 1;

        for my $y ($start_y .. $end_y) {
            for my $x (0 .. GRID_SIZE - 1) {
                my $next_state = calculate_next_state($grid, $x, $y);
                $grid->set($x, $y, $next_state);
            }
        }
        sleep(0.1);
    }
}

sub analyze_patterns {
    my ($grid) = @_;
    my %pattern_counts;

    for my $y (0 .. GRID_SIZE - 1) {
        for my $x (0 .. GRID_SIZE - 1) {
            $pattern_counts{"live_$x-$y"}++ if $grid->get($x, $y);
        }
    }
    return \%pattern_counts; 
}

sub save_pattern {
    my ($grid, $pattern_label) = @_;
    my $pattern_data = {
        label => $pattern_label,
        alive_cells => $grid->count(),
        grid => $grid,
    };

    my $filename = "${pattern_label}.json";
    open my $fh, '>', $filename or die "Could not open file '$filename': $!";
    print $fh to_json($pattern_data);
    close $fh;

    $minio_client->fput_object(BUCKET_NAME, $filename, $filename) or die "Failed to upload to MinIO: $!";
}

# Main function to run the Game of Life
sub main {
    my $grid = SparseGrid->new();
    generate_initial_conditions($grid);

    my @threads = map { threads->create(\&update_grid_thread, $grid, $_) } 1 .. NUM_THREADS;

    for my $iteration (0 .. MAX_ITERATIONS - 1) {
        sleep 1; # Allow threads to update

        my $patterns = analyze_patterns($grid);
        if ($iteration % 10 == 0) {
            save_pattern($grid, "pattern-$iteration");
        }

        # Joining threads gracefully
        $_->join() for @threads;
    }
}

# Execute the main procedure
main();
